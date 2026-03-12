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
import FolderIcon from "@mui/icons-material/Folder";
import DescriptionIcon from "@mui/icons-material/Description";
import Link from "next/link";
import type { ApiTreeNode } from "@/lib/api-client";
import { toSlashPath } from "@/lib/api-client";
import { fetchCached } from "@/lib/data-cache";

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
          <Box sx={{ width: 32, mr: 0.5 }} />
        )}

        {/* icon */}
        {isLeaf ? (
          <DescriptionIcon sx={{ fontSize: 18, color: "#757575", mr: 1 }} />
        ) : (
          <FolderIcon sx={{ fontSize: 18, color: "#f9a825", mr: 1 }} />
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

  const filteredTree = useMemo(() => {
    const q = search.toLowerCase().trim();
    return filterTree(tree, q);
  }, [tree, search]);

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

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Toolbar */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2, flexWrap: "wrap" }}>
        <TextField
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter monikers..."
          variant="outlined"
          size="small"
          sx={{ width: { xs: "100%", sm: 360 } }}
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
  );
}
