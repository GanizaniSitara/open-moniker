"use client";
import { useState, useEffect, useMemo, useCallback } from "react";
import {
  Box,
  TextField,
  InputAdornment,
  Typography,
  IconButton,
  Button,
  Chip,
  CircularProgress,
  LinearProgress,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import UnfoldMoreIcon from "@mui/icons-material/UnfoldMore";
import UnfoldLessIcon from "@mui/icons-material/UnfoldLess";
import FilterListIcon from "@mui/icons-material/FilterList";
import Link from "next/link";
import type { ApiTreeNode } from "@/lib/api-client";
import { toSlashPath } from "@/lib/api-client";
import { fetchCached } from "@/lib/data-cache";
import DatasetFilters from "@/components/DatasetFilters";

/** Collect all node paths in a tree (for expand-all). */
function collectPaths(nodes: ApiTreeNode[]): Set<string> {
  const paths = new Set<string>();
  function walk(n: ApiTreeNode) {
    if (n.children.length > 0) {
      paths.add(n.path);
      n.children.forEach(walk);
    }
  }
  nodes.forEach(walk);
  return paths;
}

/** Check if a node or any descendant matches the query. */
function matchesFilter(node: ApiTreeNode, q: string): boolean {
  if (
    node.name.toLowerCase().includes(q) ||
    node.path.toLowerCase().includes(q) ||
    (node.description && node.description.toLowerCase().includes(q))
  ) {
    return true;
  }
  return node.children.some((c) => matchesFilter(c, q));
}

/** Filter tree, keeping ancestors of matching nodes. */
function filterTree(nodes: ApiTreeNode[], q: string): ApiTreeNode[] {
  if (!q) return nodes;
  return nodes
    .filter((n) => matchesFilter(n, q))
    .map((n) => ({
      ...n,
      children: filterTree(n.children, q),
    }));
}

/** Collect leaf-node domain and vendor counts for facet filters.
 *  domainNames maps short codes → display names. */
function collectFacets(nodes: ApiTreeNode[], domainNames: Map<string, string>): {
  domains: Map<string, number>;
  vendors: Map<string, number>;
  domainLabelToCode: Map<string, string>;
} {
  const domains = new Map<string, number>();
  const vendors = new Map<string, number>();
  const domainLabelToCode = new Map<string, string>();
  function walk(n: ApiTreeNode) {
    if (n.has_source_binding) {
      const code = n.resolved_domain || n.domain || "Other";
      const label = domainNames.get(code) || code;
      domainLabelToCode.set(label, code);
      domains.set(label, (domains.get(label) || 0) + 1);
      if (n.vendor) {
        vendors.set(n.vendor, (vendors.get(n.vendor) || 0) + 1);
      }
    }
    n.children.forEach(walk);
  }
  nodes.forEach(walk);
  return { domains, vendors, domainLabelToCode };
}

/** Check if a node or any descendant matches the facet filters. */
function matchesFacets(node: ApiTreeNode, domainSet: Set<string>, vendorSet: Set<string>): boolean {
  if (node.has_source_binding) {
    const d = node.resolved_domain || node.domain || "Other";
    const domainOk = domainSet.size === 0 || domainSet.has(d);
    const vendorOk = vendorSet.size === 0 || (node.vendor ? vendorSet.has(node.vendor) : false);
    if (domainOk && vendorOk) return true;
  }
  return node.children.some((c) => matchesFacets(c, domainSet, vendorSet));
}

/** Filter tree by domain/vendor facets, keeping ancestors of matching leaves. */
function filterTreeByFacets(nodes: ApiTreeNode[], domainSet: Set<string>, vendorSet: Set<string>): ApiTreeNode[] {
  if (domainSet.size === 0 && vendorSet.size === 0) return nodes;
  return nodes
    .filter((n) => matchesFacets(n, domainSet, vendorSet))
    .map((n) => ({
      ...n,
      children: filterTreeByFacets(n.children, domainSet, vendorSet),
    }));
}

// ── Domain colour helper ──────────────────────────────────────────────

const DOMAIN_COLORS: Record<string, string> = {
  reference: "#1976d2",
  market: "#2e7d32",
  esg: "#6a1b9a",
  credit: "#c62828",
  operations: "#ef6c00",
  risk: "#ad1457",
  pricing: "#00838f",
};

function domainColor(domain: string | null): string {
  if (!domain) return "#757575";
  return DOMAIN_COLORS[domain.toLowerCase()] || "#546e7a";
}

// ── TreeNode component ────────────────────────────────────────────────

/** Check if a non-leaf node was truncated by depth (has no children loaded yet). */
function isTruncated(node: ApiTreeNode): boolean {
  return !node.has_source_binding && node.children.length === 0;
}

function TreeNodeRow({
  node,
  expanded,
  onToggle,
  depth,
  deepLoading,
}: {
  node: ApiTreeNode;
  expanded: Set<string>;
  onToggle: (path: string) => void;
  depth: number;
  deepLoading: boolean;
}) {
  const isExpanded = expanded.has(node.path);
  const hasChildren = node.children.length > 0;
  const truncated = isTruncated(node);
  const isLeaf = node.has_source_binding;
  // Treat truncated folders as expandable
  const isExpandable = hasChildren || truncated;

  return (
    <Box>
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          py: 0.5,
          pl: { xs: depth * 1.5, sm: depth * 2.5 },
          "&:hover": { bgcolor: "rgba(0,0,0,0.03)" },
          borderRadius: 1,
        }}
      >
        {/* expand/collapse toggle */}
        {isExpandable ? (
          <IconButton size="small" onClick={() => onToggle(node.path)} sx={{ mr: 0.5 }}>
            {isExpanded ? (
              <ExpandMoreIcon fontSize="small" />
            ) : (
              <ChevronRightIcon fontSize="small" />
            )}
          </IconButton>
        ) : (
          <Box sx={{ width: 32, mr: 0.5, display: "flex", alignItems: "center", justifyContent: "center", color: "#bbb", fontSize: 14 }}>·</Box>
        )}

        {/* name (link for leaf nodes) */}
        {isLeaf ? (
          <Link
            href={`/datasets/${toSlashPath(node.path)}`}
            style={{ textDecoration: "none", color: "#1976d2" }}
          >
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {node.name}
            </Typography>
          </Link>
        ) : (
          <Typography
            variant="body2"
            sx={{ fontWeight: 500, cursor: isExpandable ? "pointer" : "default" }}
            onClick={() => isExpandable && onToggle(node.path)}
          >
            {node.name}
          </Typography>
        )}

        {/* description snippet */}
        {node.description && (
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ ml: 1.5, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 400 }}
          >
            {node.description}
          </Typography>
        )}

        {/* badges */}
        <Box sx={{ ml: "auto", display: "flex", gap: 0.5, flexShrink: 0 }}>
          {(node.resolved_domain || node.domain) && (
            <Chip
              label={node.resolved_domain || node.domain}
              size="small"
              sx={{
                height: 20,
                fontSize: 11,
                bgcolor: domainColor(node.resolved_domain || node.domain),
                color: "white",
              }}
            />
          )}
          {node.vendor && (
            <Chip
              label={node.vendor}
              size="small"
              variant="outlined"
              sx={{ height: 20, fontSize: 11 }}
            />
          )}
          {node.source_type && (
            <Chip
              label={node.source_type}
              size="small"
              sx={{ height: 20, fontSize: 11, bgcolor: "#e3f2fd" }}
            />
          )}
        </Box>
      </Box>

      {/* children */}
      {isExpandable && isExpanded && (
        <Box>
          {truncated && deepLoading ? (
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ pl: { xs: (depth + 1) * 1.5 + 4, sm: (depth + 1) * 2.5 + 4 }, py: 0.5, display: "block" }}
            >
              Loading...
            </Typography>
          ) : (
            node.children.map((child) => (
              <TreeNodeRow
                key={child.path}
                node={child}
                expanded={expanded}
                onToggle={onToggle}
                depth={depth + 1}
                deepLoading={deepLoading}
              />
            ))
          )}
        </Box>
      )}
    </Box>
  );
}

// ── Main MonikerTree component ────────────────────────────────────────

export default function MonikerTree() {
  const [tree, setTree] = useState<ApiTreeNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [deepLoading, setDeepLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [filters, setFilters] = useState<Record<string, Set<string>>>({
    Domain: new Set(),
    Vendor: new Set(),
  });
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);
  // domain short-code → display name lookup (from cached datasets response)
  const [domainNames, setDomainNames] = useState<Map<string, string>>(new Map());

  useEffect(() => {
    // Build domain display-name map from the already-cached datasets response
    fetchCached("/api/search?q=&all=datasets").then((d) => {
      const map = new Map<string, string>();
      for (const dom of d.domains || []) {
        map.set(dom.key, dom.display_name);
      }
      setDomainNames(map);
    });
  }, []);

  useEffect(() => {
    let cancelled = false;

    // Phase 1: shallow tree (depth=1) for instant render
    fetchCached("/api/monikers?depth=1")
      .then((data: ApiTreeNode[]) => {
        if (cancelled) return;
        setTree(data);
        setExpanded(new Set(data.map((n) => n.path)));
        setLoading(false);
        setDeepLoading(true);

        // Phase 2: full tree in the background
        return fetch("/api/monikers")
          .then((r) => r.json())
          .then((fullData: ApiTreeNode[]) => {
            if (cancelled) return;
            setTree(fullData);
            setDeepLoading(false);
          });
      })
      .catch(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, []);

  const allPaths = useMemo(() => collectPaths(tree), [tree]);

  // Facet counts (computed from full tree, before filters)
  const { filterSections, facetFilteredTree } = useMemo(() => {
    const { domains, vendors, domainLabelToCode } = collectFacets(tree, domainNames);
    const sections = [
      {
        label: "Domain",
        options: [...domains.entries()]
          .sort((a, b) => b[1] - a[1])
          .map(([v, c]) => ({ value: v, label: v, count: c })),
      },
      {
        label: "Vendor",
        options: [...vendors.entries()]
          .sort((a, b) => b[1] - a[1])
          .map(([v, c]) => ({ value: v, label: v, count: c })),
      },
    ];
    // Translate display-name selections back to short codes for tree filtering
    const domainCodes = new Set<string>();
    for (const label of filters.Domain) {
      const code = domainLabelToCode.get(label);
      if (code) domainCodes.add(code);
    }
    const filtered = filterTreeByFacets(tree, domainCodes, filters.Vendor);
    return { filterSections: sections, facetFilteredTree: filtered };
  }, [tree, filters, domainNames]);

  const filteredTree = useMemo(() => {
    const q = search.toLowerCase().trim();
    return filterTree(facetFilteredTree, q);
  }, [facetFilteredTree, search]);

  // When searching, auto-expand all matching branches
  const effectiveExpanded = useMemo(() => {
    if (search.trim()) return collectPaths(filteredTree);
    return expanded;
  }, [search, filteredTree, expanded]);

  const onToggle = useCallback((path: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  }, []);

  const expandAll = useCallback(() => setExpanded(new Set(allPaths)), [allPaths]);
  const collapseAll = useCallback(() => setExpanded(new Set()), []);

  const handleFilterChange = useCallback(
    (section: string, value: string, checked: boolean) => {
      setFilters((prev) => {
        const next = { ...prev };
        const s = new Set(next[section]);
        if (checked) s.add(value);
        else s.delete(value);
        next[section] = s;
        return next;
      });
    },
    []
  );

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ display: "flex", gap: 4 }}>
      {/* Sidebar */}
      <DatasetFilters
        sections={filterSections}
        selected={filters}
        onChange={handleFilterChange}
        mobileOpen={mobileFiltersOpen}
        onMobileToggle={() => setMobileFiltersOpen(false)}
        onClear={() => setFilters({ Domain: new Set(), Vendor: new Set() })}
        onSelectAll={(section) =>
          setFilters((prev) => ({
            ...prev,
            [section]: new Set(
              filterSections
                .find((s) => s.label === section)
                ?.options.map((o) => o.value) || []
            ),
          }))
        }
      />

      {/* Main content */}
      <Box sx={{ flexGrow: 1, minWidth: 0 }}>
        <Button
          startIcon={<FilterListIcon />}
          onClick={() => setMobileFiltersOpen(true)}
          variant="outlined"
          size="small"
          sx={{ display: { xs: "inline-flex", md: "none" }, mb: 1 }}
        >
          Filters
        </Button>

        {/* Toolbar */}
        <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2, flexWrap: "wrap" }}>
          <TextField
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filter monikers..."
            variant="outlined"
            size="small"
            sx={{ flexGrow: 1 }}
            slotProps={{
              input: {
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon sx={{ color: "#53565A" }} />
                  </InputAdornment>
                ),
              },
            }}
          />
          <Button size="small" startIcon={<UnfoldMoreIcon />} onClick={expandAll}>
            Expand all
          </Button>
          <Button size="small" startIcon={<UnfoldLessIcon />} onClick={collapseAll}>
            Collapse all
          </Button>
        </Box>

        {/* Deep-loading progress indicator */}
        {deepLoading && (
          <Box sx={{ mb: 1 }}>
            <LinearProgress sx={{ borderRadius: 1 }} />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: "block" }}>
              Loading full tree...
            </Typography>
          </Box>
        )}

        {/* Tree */}
        {filteredTree.length === 0 ? (
          <Typography color="text.secondary" sx={{ py: 4, textAlign: "center" }}>
            {search ? "No monikers match your filter." : "No monikers found."}
          </Typography>
        ) : (
          <Box sx={{ fontFamily: "monospace" }}>
            {filteredTree.map((node) => (
              <TreeNodeRow
                key={node.path}
                node={node}
                expanded={effectiveExpanded}
                onToggle={onToggle}
                depth={0}
                deepLoading={deepLoading}
              />
            ))}
          </Box>
        )}
      </Box>
    </Box>
  );
}
