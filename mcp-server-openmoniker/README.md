# MCP Server for Open Moniker

An [MCP](https://modelcontextprotocol.io/) server that exposes the Open Moniker data catalog to AI coding assistants. Browse the catalog, resolve monikers, inspect ownership, search for data assets, and submit governance requests — all from your editor.

## Quick Start

```bash
cd mcp-server-openmoniker
pip install -e .
python server.py          # starts on localhost:8051
```

The server prints a **write token** on startup (only needed for write operations — reads are anonymous).

## Adding to Claude Code

**HTTP transport (recommended — server must already be running):**

```bash
claude mcp add --transport http --scope user open-moniker http://localhost:8051/mcp
```

**stdio transport (Claude Code launches the server for you):**

```bash
claude mcp add --transport stdio --scope user open-moniker \
  -- python /path/to/open-moniker/mcp-server-openmoniker/server.py --transport stdio
```

Use `--scope project` instead of `--scope user` to store the config in `.mcp.json` (shared with the team) rather than your personal settings.

Verify it's registered:

```bash
claude mcp list
```

Remove it later with:

```bash
claude mcp remove open-moniker
```

## Adding to OpenCode

OpenCode uses a config file. Add to `.opencode.json` (project root or `~/.opencode.json`):

```json
{
  "mcpServers": {
    "open-moniker": {
      "type": "stdio",
      "command": "python",
      "args": ["/path/to/open-moniker/mcp-server-openmoniker/server.py", "--transport", "stdio"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MCP_PORT` | `8051` | Server port |
| `MCP_HOST` | `0.0.0.0` | Bind address |
| `MCP_WRITE_TOKEN` | *(auto-generated)* | Bearer token for write operations |
| `CATALOG_YAML` | `../sample_catalog.yaml` | Path to catalog definition |
| `DOMAINS_YAML` | `../sample_domains.yaml` | Path to domains definition |
| `MODELS_YAML` | `../sample_models.yaml` | Path to models definition |

To pass env vars in Claude Code:

```bash
claude mcp add --transport stdio --scope user \
  --env CATALOG_YAML=/data/catalog.yaml \
  --env MCP_WRITE_TOKEN=my-secret-token \
  open-moniker \
  -- python /path/to/open-moniker/mcp-server-openmoniker/server.py --transport stdio
```

## Available Tools

### Read (no auth)

| Tool | Description |
|---|---|
| `resolve_moniker` | Resolve a moniker to source connection info (type, query, params) |
| `list_children` | List direct children of a catalog path |
| `describe_moniker` | Full metadata: ownership, schema, data quality, docs |
| `search_catalog` | Full-text search across paths, names, descriptions, tags |
| `get_lineage` | Ownership lineage — where each role is defined |
| `get_catalog_tree` | Browse the catalog as a nested tree |
| `get_catalog_stats` | Summary counts by status and source type |
| `get_domains` | List all data domains |
| `get_models` | List all business models/measures |
| `get_model_detail` | Details for a specific model (formula, ownership, appearances) |

### Write (require `MCP_WRITE_TOKEN`)

| Tool | Description |
|---|---|
| `submit_request` | Submit a moniker creation request for governance review |
| `list_requests` | List requests, optionally filtered by status |
| `approve_request` | Approve a pending request and activate the moniker |
| `reject_request` | Reject a pending request |
| `update_node_status` | Change a node's lifecycle status |

### Prompts

| Prompt | Description |
|---|---|
| `explore_domain` | Walk through a domain's monikers, ownership, and sources |
| `find_data` | Find data assets by keyword |
| `check_ownership` | Investigate ownership for a moniker or domain |

## Example Queries

Once connected, ask your AI assistant things like:

- *"What data domains are available?"*
- *"Search the catalog for treasury data"*
- *"Who owns risk.cvar?"*
- *"Resolve the moniker for prices.equity/AAPL"*
- *"Show me the schema for fixed_income/govies/treasury"*
- *"Submit a request for a new moniker under prices"*
