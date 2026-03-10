"use client";
import { useState, useMemo, useCallback, useEffect } from "react";
import {
  Container,
  Typography,
  Box,
  TextField,
  InputAdornment,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import FieldCard from "@/components/FieldCard";
import DatasetFilters from "@/components/DatasetFilters";

interface FieldItem {
  key: string;
  display_name: string;
  description?: string;
  formula?: string;
  unit?: string;
  semantic_tags?: string[];
  containerName: string;
  datasetCount: number;
}

export default function FieldBrowser() {
  const [searchQuery, setSearchQuery] = useState("");
  const [fields, setFields] = useState<FieldItem[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [filters, setFilters] = useState<Record<string, Set<string>>>({
    Group: new Set(),
    Tags: new Set(),
  });

  useEffect(() => {
    fetch("/api/search?all=fields")
      .then((r) => r.json())
      .then((d) => {
        setFields(d.fields || []);
        setLoaded(true);
      });
  }, []);

  // Step 1: filter by search text
  const searchFiltered = useMemo(() => {
    let result = fields;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (f) =>
          f.display_name.toLowerCase().includes(q) ||
          (f.description || "").toLowerCase().includes(q)
      );
    }
    return result;
  }, [fields, searchQuery]);

  // Step 2: compute facet counts from search-filtered results
  const filterSections = useMemo(() => {
    const groupCounts = new Map<string, number>();
    const tagCounts = new Map<string, number>();

    for (const f of searchFiltered) {
      const group = f.containerName || "Other";
      groupCounts.set(group, (groupCounts.get(group) || 0) + 1);
      for (const tag of f.semantic_tags || []) {
        tagCounts.set(tag, (tagCounts.get(tag) || 0) + 1);
      }
    }

    return [
      {
        label: "Group",
        options: [...groupCounts.entries()]
          .sort((a, b) => b[1] - a[1])
          .map(([v, c]) => ({ value: v, label: v, count: c })),
      },
      {
        label: "Tags",
        options: [...tagCounts.entries()]
          .sort((a, b) => b[1] - a[1])
          .map(([v, c]) => ({ value: v, label: v, count: c })),
      },
    ];
  }, [searchFiltered]);

  // Step 3: apply facet filters to search-filtered results
  const displayedFields = useMemo(() => {
    let result = searchFiltered;

    if (filters.Group.size > 0) {
      result = result.filter((f) =>
        filters.Group.has(f.containerName || "Other")
      );
    }
    if (filters.Tags.size > 0) {
      result = result.filter((f) =>
        f.semantic_tags?.some((tag) => filters.Tags.has(tag))
      );
    }

    result.sort((a, b) => a.display_name.localeCompare(b.display_name));
    return result;
  }, [searchFiltered, filters]);

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

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Box sx={{ display: "flex", gap: 4 }}>
        {/* Sidebar */}
        <DatasetFilters
          sections={filterSections}
          selected={filters}
          onChange={handleFilterChange}
          onClear={() =>
            setFilters({
              Group: new Set(),
              Tags: new Set(),
            })
          }
        />

        {/* Field cards */}
        <Box sx={{ flexGrow: 1, minWidth: 0 }}>
          <TextField
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search fields..."
            fullWidth
            variant="outlined"
            size="small"
            sx={{ mb: 1 }}
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

          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {loaded ? `${displayedFields.length} fields` : "Loading..."}
          </Typography>

          {displayedFields.map((f) => (
            <FieldCard
              key={f.key}
              fieldKey={f.key}
              displayName={f.display_name}
              description={f.description}
              formula={f.formula}
              unit={f.unit}
              datasetCount={f.datasetCount}
              semanticTags={f.semantic_tags}
            />
          ))}
        </Box>
      </Box>
    </Container>
  );
}
