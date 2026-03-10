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
import DatasetCard from "@/components/DatasetCard";
import DatasetFilters from "@/components/DatasetFilters";
import type { Dataset, Domain } from "@/lib/types";

export default function CatalogBrowser() {
  const [searchQuery, setSearchQuery] = useState("");
  const [datasets, setDatasets] = useState<
    (Dataset & { domainDisplayName?: string; domainColor?: string })[]
  >([]);
  const [, setDomains] = useState<Domain[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [filters, setFilters] = useState<Record<string, Set<string>>>({
    Category: new Set(),
    Fields: new Set(),
  });

  useEffect(() => {
    fetch("/api/search?q=&all=datasets")
      .then((r) => r.json())
      .then((d) => {
        setDatasets(d.datasets || []);
        setDomains(d.domains || []);
        setLoaded(true);
      });
  }, []);

  // Step 1: filter by search text
  const searchFiltered = useMemo(() => {
    let result = datasets.filter((ds) => !ds.isContainer);
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (ds) =>
          ds.key.toLowerCase().includes(q) ||
          ds.display_name.toLowerCase().includes(q) ||
          (ds.description || "").toLowerCase().includes(q)
      );
    }
    return result;
  }, [datasets, searchQuery]);

  // Step 2: compute facet counts from search-filtered results
  const filterSections = useMemo(() => {
    const categoryCounts = new Map<string, number>();
    const fieldCounts = new Map<string, number>();

    for (const ds of searchFiltered) {
      const cat = ds.domainDisplayName || "Other";
      categoryCounts.set(cat, (categoryCounts.get(cat) || 0) + 1);
      for (const col of ds.schema?.columns || []) {
        fieldCounts.set(col.name, (fieldCounts.get(col.name) || 0) + 1);
      }
    }

    return [
      {
        label: "Category",
        options: [...categoryCounts.entries()]
          .sort((a, b) => b[1] - a[1])
          .map(([v, c]) => ({ value: v, label: v, count: c })),
      },
      {
        label: "Fields",
        options: [...fieldCounts.entries()]
          .sort((a, b) => b[1] - a[1])
          .map(([v, c]) => ({ value: v, label: v, count: c })),
      },
    ];
  }, [searchFiltered]);

  // Step 3: apply facet filters to search-filtered results
  const displayedDatasets = useMemo(() => {
    let result = searchFiltered;

    if (filters.Category.size > 0) {
      result = result.filter((ds) =>
        filters.Category.has(ds.domainDisplayName || "Other")
      );
    }
    if (filters.Fields.size > 0) {
      result = result.filter((ds) =>
        ds.schema?.columns?.some((col) => filters.Fields.has(col.name))
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
              Category: new Set(),
              Fields: new Set(),
            })
          }
        />

        {/* Dataset cards */}
        <Box sx={{ flexGrow: 1, minWidth: 0 }}>
          <TextField
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search datasets..."
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
            {loaded ? `${displayedDatasets.length} datasets` : "Loading..."}
          </Typography>

          {displayedDatasets.map((ds) => (
            <DatasetCard
              key={ds.key}
              datasetKey={ds.key}
              displayName={ds.display_name}
              description={ds.description}
              sourceType={ds.source_binding?.type}
              domainDisplayName={ds.domainDisplayName}
              domainColor={ds.domainColor}
              columnCount={ds.schema?.columns?.length || 0}
              classification={ds.classification}
              isContainer={ds.isContainer}
              columns={ds.schema?.columns || []}
            />
          ))}
        </Box>
      </Box>
    </Container>
  );
}
