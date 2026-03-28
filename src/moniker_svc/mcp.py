"""Embedded MCP server — read-only tools mounted on /mcp within the monolith.

Exposes the same catalog, domains, models, and governance metadata as the
standalone MCP server, but runs in-process with the FastAPI app and shares
its registries (no duplicate YAML loading).

Write tools (submit/approve/reject) are intentionally excluded.

Transport: Streamable HTTP — a single endpoint at /mcp/ (POST|GET|DELETE)
when mounted at /mcp on the FastAPI app.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from mcp.server.fastmcp import FastMCP

from .telemetry.events import CallerIdentity

logger = logging.getLogger("mcp-openmoniker")

# ---------------------------------------------------------------------------
# Shared state — populated by configure() from the main app lifespan
# ---------------------------------------------------------------------------

@dataclass
class _McpState:
    catalog: Any
    domain_registry: Any
    model_registry: Any
    request_registry: Any
    service: Any
    config: Any


_state: _McpState | None = None


def configure(
    *,
    catalog,
    service,
    domain_registry,
    model_registry,
    request_registry,
    config,
) -> None:
    """Set the shared state from the main app lifespan."""
    global _state
    _state = _McpState(
        catalog=catalog,
        domain_registry=domain_registry,
        model_registry=model_registry,
        request_registry=request_registry,
        service=service,
        config=config,
    )
    logger.info("MCP module configured (read-only, %d catalog paths)", len(catalog.all_paths()))


def _require_state() -> _McpState:
    if _state is None:
        raise RuntimeError("MCP module not configured — call configure() during lifespan")
    return _state


# ---------------------------------------------------------------------------
# Create the FastMCP server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="open-moniker",
    streamable_http_path="/",
    instructions=(
        "Moniker Service MCP Server — a unified data catalog and governance layer for firm-wide data access.\n\n"

        "## What is a Moniker?\n"
        "A moniker is a human-readable, hierarchical path that identifies a data asset. "
        "It resolves to a source system (Snowflake, Oracle, MS-SQL, REST, Excel, etc.) "
        "without the caller needing to know connection strings, credentials, or query syntax.\n\n"

        "## Path Structure\n"
        "Monikers follow the pattern:  domain[.subdomain]/[segments]\n\n"
        "  Dots (.)  separate logical groupings within a domain namespace:\n"
        "            risk.cvar, credit.exposures, rates.swap\n\n"
        "  Slashes (/) separate navigable path segments used for filtering:\n"
        "            fixed.income/govies/treasury\n"
        "            fixed.income/govies/sovereign/DE        <- filter to Germany\n"
        "            fixed.income/govies/sovereign/DE/10Y    <- filter to German 10Y\n\n"
        "  Segments after the leaf moniker act as query filters. "
        "Omitting a segment returns all values for that dimension. "
        "Never use 'ALL' — just omit the segment.\n\n"

        "## Browsing the Catalog\n"
        "  - Call `get_catalog_tree()` for the full hierarchy\n"
        "  - Call `list_children('risk')` to see what's under a domain\n"
        "  - Call `search_catalog('treasury')` to find assets by keyword\n"
        "  - Call `describe_moniker('credit.exposures')` for schema and ownership\n"
        "  - Read resource `moniker://about` for full conventions and examples\n"
        "  - Read resource `moniker://naming-guide` for patterns from the live catalog\n\n"

        "## Note\n"
        "This is a read-only MCP endpoint. To submit or approve moniker requests, "
        "use the REST API at /requests."
    ),
)


# ---------------------------------------------------------------------------
# Helper: anonymous caller identity for read tools
# ---------------------------------------------------------------------------

_MCP_CALLER = CallerIdentity(
    service_id="mcp-server",
    user_id=None,
    app_id="mcp-openmoniker",
    team=None,
    claims={},
)


def _node_to_dict(node) -> dict[str, Any]:
    """Serialise a CatalogNode to a JSON-friendly dict."""
    d: dict[str, Any] = {
        "path": node.path,
        "display_name": node.display_name,
        "description": node.description,
        "status": node.status.value if hasattr(node.status, "value") else str(node.status),
        "is_leaf": node.is_leaf,
    }
    if node.ownership:
        d["ownership"] = {}
        for attr in ("accountable_owner", "data_specialist", "support_channel", "adop", "ads", "adal"):
            v = getattr(node.ownership, attr, None)
            if v:
                d["ownership"][attr] = v
    if node.source_binding:
        d["source_type"] = node.source_binding.source_type.value
    if node.classification:
        d["classification"] = node.classification
    if node.tags:
        d["tags"] = list(node.tags)
    if node.successor:
        d["successor"] = node.successor
    if node.deprecation_message:
        d["deprecation_message"] = node.deprecation_message
    return d


def _ownership_to_dict(ownership) -> dict[str, Any]:
    """Serialise ResolvedOwnership to dict."""
    d: dict[str, Any] = {}
    for attr in (
        "accountable_owner", "accountable_owner_source",
        "data_specialist", "data_specialist_source",
        "support_channel", "support_channel_source",
        "adop", "adop_source", "ads", "ads_source", "adal", "adal_source",
    ):
        v = getattr(ownership, attr, None)
        if v:
            d[attr] = v
    return d


# ===================================================================
# READ TOOLS  (anonymous — no auth required)
# ===================================================================

@mcp.tool(
    name="resolve_moniker",
    description=(
        "Resolve a moniker path to source connection info. "
        "Returns source_type, connection parameters, query, ownership, "
        "and binding metadata.  Example: resolve_moniker('risk.cvar/758-A/USD/ALL')"
    ),
)
async def resolve_moniker(moniker: str) -> str:
    """Resolve a moniker to its source connection info."""
    s = _require_state()
    try:
        result = await s.service.resolve(moniker, _MCP_CALLER)
        return json.dumps({
            "moniker": result.moniker,
            "path": result.path,
            "source_type": result.source.source_type,
            "connection": result.source.connection,
            "query": result.source.query,
            "params": result.source.params,
            "read_only": result.source.read_only,
            "ownership": _ownership_to_dict(result.ownership),
            "binding_path": result.binding_path,
            "sub_path": result.sub_path,
            "redirected_from": result.redirected_from,
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)})


@mcp.tool(
    name="list_children",
    description=(
        "List the direct children of a moniker path in the catalog. "
        "Example: list_children('risk') -> ['cvar', 'greeks', 'limits', ...]"
    ),
)
async def list_children(path: str) -> str:
    """List children of a catalog path."""
    s = _require_state()
    try:
        result = await s.service.list_children(path, _MCP_CALLER)
        return json.dumps({
            "path": result.path,
            "children": result.children,
            "count": len(result.children),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)})


@mcp.tool(
    name="describe_moniker",
    description=(
        "Get metadata for a moniker path: display name, description, ownership, "
        "source type, data quality, schema, documentation links, and related models. "
        "Example: describe_moniker('fixed.income/govies/treasury')"
    ),
)
async def describe_moniker(path: str) -> str:
    """Describe a moniker path's metadata."""
    s = _require_state()
    try:
        result = await s.service.describe(path, _MCP_CALLER)
        d: dict[str, Any] = {
            "path": result.path,
            "has_source_binding": result.has_source_binding,
            "source_type": result.source_type,
            "ownership": _ownership_to_dict(result.ownership),
        }
        if result.node:
            d["display_name"] = result.node.display_name
            d["description"] = result.node.description
            d["status"] = result.node.status.value if hasattr(result.node.status, "value") else str(result.node.status)
            if result.node.classification:
                d["classification"] = result.node.classification
            if result.node.tags:
                d["tags"] = list(result.node.tags)
            if result.node.data_quality:
                dq = result.node.data_quality
                d["data_quality"] = {
                    "dq_owner": dq.dq_owner,
                    "quality_score": dq.quality_score,
                    "known_issues": list(dq.known_issues) if dq.known_issues else [],
                }
            if result.node.data_schema:
                d["schema"] = {
                    "columns": [
                        {"name": c.name, "type": c.data_type, "description": c.description, "semantic_type": c.semantic_type}
                        for c in result.node.data_schema.columns
                    ] if result.node.data_schema.columns else [],
                    "semantic_tags": list(result.node.data_schema.semantic_tags) if result.node.data_schema.semantic_tags else [],
                }
            if result.node.documentation:
                doc = result.node.documentation
                d["documentation"] = {}
                for attr in ("glossary", "runbook", "data_dictionary", "onboarding"):
                    v = getattr(doc, attr, None)
                    if v:
                        d["documentation"][attr] = v
            if result.node.successor:
                d["successor"] = result.node.successor
            if result.node.deprecation_message:
                d["deprecation_message"] = result.node.deprecation_message
        models = s.model_registry.models_for_moniker(result.path)
        if models:
            d["models"] = [
                {"path": m.path, "display_name": m.display_name, "unit": m.unit, "formula": m.formula}
                for m in models
            ]
        return json.dumps(d, indent=2)
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)})


@mcp.tool(
    name="search_catalog",
    description=(
        "Full-text search across the catalog by path, display name, description, "
        "or tags.  Returns up to `limit` matching nodes. "
        "Example: search_catalog('treasury') or search_catalog('credit risk')"
    ),
)
async def search_catalog(query: str, limit: int = 20) -> str:
    """Search catalog nodes."""
    s = _require_state()
    results = s.catalog.search(query, limit=limit)
    return json.dumps({
        "query": query,
        "results": [_node_to_dict(n) for n in results],
        "count": len(results),
    }, indent=2)


@mcp.tool(
    name="get_lineage",
    description=(
        "Get the ownership lineage for a moniker path — shows the full path "
        "hierarchy and where each ownership field was defined. "
        "Example: get_lineage('risk.cvar')"
    ),
)
async def get_lineage(path: str) -> str:
    """Get ownership lineage for a path."""
    s = _require_state()
    try:
        result = await s.service.lineage(path, _MCP_CALLER)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)})


@mcp.tool(
    name="get_catalog_tree",
    description=(
        "Get the catalog as a tree rooted at an optional path. "
        "Returns nested children for browsing.  Call with no args for the "
        "full top-level tree, or pass a path to get a subtree."
    ),
)
async def get_catalog_tree(root_path: str = "") -> str:
    """Get catalog tree from a given root."""
    s = _require_state()

    def _build_tree(path: str) -> list[dict[str, Any]]:
        children_paths = s.catalog.children_paths(path)
        nodes = []
        for cp in sorted(children_paths):
            node = s.catalog.get(cp)
            if not node:
                continue
            entry: dict[str, Any] = {
                "path": cp,
                "name": cp.split("/")[-1].split(".")[-1],
                "display_name": node.display_name,
                "is_leaf": node.is_leaf,
            }
            if node.source_binding:
                entry["source_type"] = node.source_binding.source_type.value
            sub = _build_tree(cp)
            if sub:
                entry["children"] = sub
            nodes.append(entry)
        return nodes

    tree = _build_tree(root_path)
    return json.dumps({"root": root_path or "(top)", "tree": tree, "count": len(tree)}, indent=2)


@mcp.tool(
    name="get_catalog_stats",
    description="Get summary statistics for the catalog: total monikers, counts by status and source type.",
)
async def get_catalog_stats() -> str:
    """Get catalog statistics."""
    s = _require_state()
    counts = s.catalog.count()
    source_types: dict[str, int] = {}
    for node in s.catalog.all_nodes():
        if node.source_binding:
            st = node.source_binding.source_type.value
            source_types[st] = source_types.get(st, 0) + 1
    return json.dumps({
        "status_counts": counts,
        "source_type_counts": source_types,
        "domain_count": s.domain_registry.count(),
        "model_count": s.model_registry.count(),
    }, indent=2)


@mcp.tool(
    name="get_domains",
    description="List all data domains with their metadata (owner, category, confidentiality, etc.).",
)
async def get_domains() -> str:
    """List all domains."""
    s = _require_state()
    domains = s.domain_registry.all_domains()
    return json.dumps({
        "domains": [
            {
                "name": d.name,
                "display_name": d.display_name,
                "short_code": d.short_code,
                "data_category": d.data_category,
                "owner": d.owner,
                "tech_custodian": d.tech_custodian,
                "confidentiality": d.confidentiality,
                "help_channel": d.help_channel,
            }
            for d in domains
        ],
        "count": len(domains),
    }, indent=2)


@mcp.tool(
    name="get_models",
    description=(
        "List all business models/measures registered in the catalog. "
        "Each model describes a metric (like DV01, Alpha, Sharpe) that can "
        "appear across multiple monikers."
    ),
)
async def get_models() -> str:
    """List all business models."""
    s = _require_state()
    models = s.model_registry.all_models()
    return json.dumps({
        "models": [
            {
                "path": m.path,
                "display_name": m.display_name,
                "description": m.description,
                "formula": m.formula,
                "unit": m.unit,
                "semantic_tags": list(m.semantic_tags),
            }
            for m in models
        ],
        "count": len(models),
    }, indent=2)


@mcp.tool(
    name="get_model_detail",
    description=(
        "Get full details for a specific business model, including formula, "
        "ownership, and the moniker patterns where it appears. "
        "Example: get_model_detail('risk.analytics/dv01')"
    ),
)
async def get_model_detail(model_path: str) -> str:
    """Get a single model's details."""
    s = _require_state()
    model = s.model_registry.get(model_path)
    if model is None:
        return json.dumps({"error": "not_found", "message": f"Model not found: {model_path}"})
    return json.dumps({
        "path": model.path,
        "display_name": model.display_name,
        "description": model.description,
        "formula": model.formula,
        "unit": model.unit,
        "data_type": model.data_type,
        "ownership": {
            "methodology_owner": model.ownership.methodology_owner if model.ownership else None,
            "business_steward": model.ownership.business_steward if model.ownership else None,
        },
        "documentation_url": model.documentation_url,
        "appears_in": [
            {"moniker_pattern": link.moniker_pattern, "column_name": link.column_name, "notes": link.notes}
            for link in model.appears_in
        ],
        "semantic_tags": list(model.semantic_tags),
    }, indent=2)


# ===================================================================
# RESOURCES  (browseable data for MCP clients)
# ===================================================================

@mcp.resource(
    "moniker://catalog",
    name="catalog_overview",
    description="Overview of all catalog paths with status counts",
    mime_type="application/json",
)
async def catalog_overview() -> str:
    s = _require_state()
    paths = sorted(s.catalog.all_paths())
    counts = s.catalog.count()
    return json.dumps({"paths": paths, "counts": counts}, indent=2)


@mcp.resource(
    "moniker://catalog/{path}",
    name="catalog_node",
    description="Detailed info for a specific catalog node",
    mime_type="application/json",
)
async def catalog_node(path: str) -> str:
    s = _require_state()
    node = s.catalog.get(path)
    if node is None:
        return json.dumps({"error": "not_found", "path": path})
    d = _node_to_dict(node)
    children = s.catalog.children_paths(path)
    if children:
        d["children"] = sorted(children)
    ownership = s.catalog.resolve_ownership(path, s.domain_registry)
    d["resolved_ownership"] = _ownership_to_dict(ownership)
    return json.dumps(d, indent=2)


@mcp.resource(
    "moniker://domains",
    name="domains_list",
    description="All registered data domains",
    mime_type="application/json",
)
async def domains_list() -> str:
    s = _require_state()
    domains = s.domain_registry.all_domains()
    return json.dumps({
        "domains": [
            {
                "name": d.name,
                "display_name": d.display_name,
                "short_code": d.short_code,
                "data_category": d.data_category,
                "color": d.color,
                "owner": d.owner,
                "tech_custodian": d.tech_custodian,
                "business_steward": d.business_steward,
                "confidentiality": d.confidentiality,
                "pii": d.pii,
                "help_channel": d.help_channel,
                "wiki_link": d.wiki_link,
                "notes": d.notes,
            }
            for d in domains
        ],
    }, indent=2)


@mcp.resource(
    "moniker://about",
    name="about",
    description=(
        "Full self-description of Moniker Service: what it is, how monikers are structured, "
        "path conventions, segment filtering, and how to design a moniker hierarchy."
    ),
    mime_type="text/markdown",
)
async def about() -> str:
    s = _require_state()
    stats = s.catalog.count()
    source_types: dict[str, int] = {}
    for node in s.catalog.all_nodes():
        if node.source_binding:
            st = node.source_binding.source_type.value
            source_types[st] = source_types.get(st, 0) + 1

    top_level_paths = sorted(s.catalog.children_paths(""))
    domain_names = ", ".join(f"`{p}`" for p in top_level_paths[:12])
    source_summary = ", ".join(f"{v} {k}" for k, v in sorted(source_types.items(), key=lambda x: -x[1]))

    return (
        "# Moniker Service — Self-Description\n\n"
        "## What Is Moniker Service?\n"
        "Moniker Service is a unified data catalog and governance layer. It lets you access\n"
        "any data asset across the firm using a single, human-readable path (a \"moniker\")\n"
        "without knowing connection strings, credentials, SQL dialects, or API shapes.\n\n"
        f"## This Catalog\n"
        f"- **Total monikers**: {sum(stats.values())}\n"
        f"- **Source systems**: {source_summary}\n"
        f"- **Top-level domains**: {domain_names}\n\n"
        "## Moniker Path Structure\n\n"
        "```\n"
        "domain[.subdomain]/[filter_segment_1]/[filter_segment_2]\n"
        "```\n\n"
        "| Pattern | Example | Meaning |\n"
        "|---------|---------|---------||\n"
        "| `domain.leaf` | `credit.exposures` | Counterparty credit exposure data |\n"
        "| `domain.leaf/seg` | `rates.swap/USD` | USD swap rates only |\n"
        "| `domain/sub/leaf` | `fixed.income/govies/treasury` | All US Treasury data |\n"
        "| `domain/sub/leaf/filter` | `fixed.income/govies/sovereign/DE` | German Bunds only |\n\n"
        "## Conventions\n\n"
        "- **Dots** (`.`) group logical sub-namespaces: `risk.cvar`, `risk.greeks`\n"
        "- **Slashes** (`/`) create navigable hierarchy: `fixed.income/govies/treasury`\n"
        "- **Never use `ALL`** — just omit the segment to get all values.\n\n"
        "## REST API (Alternative to MCP)\n"
        "The same data is also available via REST on this server.\n"
        "- OpenAPI JSON spec: `/openapi.json`\n"
        "- Swagger UI: `/docs`\n"
    )


@mcp.resource(
    "moniker://naming-guide",
    name="naming_guide",
    description=(
        "Live naming-guide generated from the actual catalog — shows real moniker patterns, "
        "segment conventions, and examples to help LLMs design moniker hierarchies."
    ),
    mime_type="text/markdown",
)
async def naming_guide() -> str:
    s = _require_state()

    leaves: list[dict] = []
    for node in s.catalog.all_nodes():
        if node.is_leaf and node.source_binding:
            entry: dict = {
                "path": node.path,
                "source_type": node.source_binding.source_type.value,
                "display_name": node.display_name or "",
                "description": node.description or "",
            }
            leaves.append(entry)

    leaves.sort(key=lambda x: x["path"])

    lines = [
        "# Moniker Service — Live Naming Guide",
        "",
        "This guide is generated from the live catalog and shows real moniker patterns.",
        "",
        "## Leaf Monikers (Data Assets)",
        "",
        "| Moniker Path | Source | Description |",
        "|---|---|---|",
    ]
    for leaf in leaves:
        desc = leaf["description"][:60] + "…" if len(leaf.get("description", "")) > 60 else leaf.get("description", "")
        lines.append(f"| `{leaf['path']}` | {leaf['source_type']} | {desc} |")

    lines += ["", "## Fetch Examples", "", "```python", "# All data — omit segments"]
    for leaf in leaves[:3]:
        lines.append(f'client.fetch("{leaf["path"]}")')

    lines += ["```", "", "## Domain Structure", ""]

    top_paths = sorted(s.catalog.children_paths(""))
    for tp in top_paths:
        node = s.catalog.get(tp)
        desc = node.description or node.display_name or "" if node else ""
        children = s.catalog.children_paths(tp)
        lines.append(f"### `{tp}` ({len(children)} children)")
        if desc:
            lines.append(f"{desc}")
        lines.append("")
        for cp in sorted(children)[:6]:
            cnode = s.catalog.get(cp)
            cdesc = cnode.display_name or "" if cnode else ""
            is_leaf = cnode.is_leaf if cnode else False
            source = f" [{cnode.source_binding.source_type.value}]" if cnode and cnode.source_binding else ""
            lines.append(f"  - `{cp}`{source} — {cdesc}{'  *(leaf)*' if is_leaf else ''}")
        if len(children) > 6:
            lines.append(f"  - *(+ {len(children) - 6} more)*")
        lines.append("")

    return "\n".join(lines)


@mcp.resource(
    "moniker://models",
    name="models_list",
    description="All registered business models/measures",
    mime_type="application/json",
)
async def models_list() -> str:
    s = _require_state()
    models = s.model_registry.all_models()
    return json.dumps({
        "models": [
            {
                "path": m.path,
                "display_name": m.display_name,
                "description": m.description,
                "formula": m.formula,
                "unit": m.unit,
                "semantic_tags": list(m.semantic_tags),
                "appears_in_count": len(m.appears_in),
            }
            for m in models
        ],
    }, indent=2)


# ===================================================================
# PROMPTS  (reusable conversation templates)
# ===================================================================

@mcp.prompt(
    name="explore_domain",
    description="Walk through a data domain — lists its monikers, ownership, and source types.",
)
async def explore_domain_prompt(domain_name: str) -> str:
    return (
        f"I'd like to explore the **{domain_name}** data domain.\n\n"
        f"1. First, call `get_domains` to see if '{domain_name}' exists and get its metadata.\n"
        f"2. Then call `get_catalog_tree(root_path='{domain_name}')` to see all monikers under it.\n"
        f"3. For any interesting leaf moniker, call `describe_moniker` to see its schema and ownership.\n"
        f"4. If you want connection details, call `resolve_moniker` on a specific path.\n\n"
        f"Please summarise what data is available under {domain_name}, who owns it, "
        f"and what source systems it comes from."
    )


@mcp.prompt(
    name="find_data",
    description="Help find a specific data asset by keyword or description.",
)
async def find_data_prompt(keyword: str) -> str:
    return (
        f"I'm looking for data related to **{keyword}**.\n\n"
        f"1. Call `search_catalog(query='{keyword}')` to find matching monikers.\n"
        f"2. For each result, call `describe_moniker` to get ownership and schema details.\n"
        f"3. If the data has related business models, call `get_models` filtered by relevant tags.\n\n"
        f"Please summarise what you find: the moniker paths, what data they contain, "
        f"who owns them, and how to access them."
    )


@mcp.prompt(
    name="design_moniker_hierarchy",
    description="Guide an LLM or user through designing a moniker hierarchy for their firm or team.",
)
async def design_moniker_hierarchy_prompt(use_case: str) -> str:
    return (
        f"I need to design a moniker hierarchy for: **{use_case}**\n\n"
        f"Please help me by:\n\n"
        f"1. First read `moniker://about` to understand the full moniker path conventions.\n\n"
        f"2. Then read `moniker://naming-guide` to see real patterns from the live catalog.\n\n"
        f"3. Based on the conventions and live examples, propose a moniker hierarchy for: **{use_case}**\n"
        f"   - Suggest top-level domain name(s)\n"
        f"   - Show the full path structure including any sub-paths\n"
        f"   - Identify which dimensions should be filter segments\n"
        f"   - Explain why you chose dots vs slashes at each level\n"
        f"   - Give 3-5 concrete example moniker paths\n\n"
        f"4. Check if any similar patterns already exist using `search_catalog`.\n\n"
        f"Present the proposed hierarchy as a table and then as example `client.fetch()` calls."
    )


@mcp.prompt(
    name="check_ownership",
    description="Investigate who is responsible for a particular moniker or domain.",
)
async def check_ownership_prompt(path: str) -> str:
    return (
        f"I need to understand ownership for **{path}**.\n\n"
        f"1. Call `get_lineage(path='{path}')` to see the full ownership chain.\n"
        f"2. Note where each role (ADOP, ADS, ADAL, accountable_owner) is defined.\n"
        f"3. If the ownership comes from a domain fallback, note that.\n\n"
        f"Please present the ownership hierarchy clearly, showing which fields are "
        f"inherited and from where."
    )


# ---------------------------------------------------------------------------
# ASGI app factory — called from main.py to mount on /mcp
# ---------------------------------------------------------------------------

def get_streamable_http_app():
    """Return the MCP streamable HTTP Starlette ASGI app for mounting on FastAPI.

    When mounted at ``/mcp`` on the FastAPI app the endpoint becomes:
      POST|GET|DELETE  /mcp/  — streamable HTTP transport
    """
    return mcp.streamable_http_app()
