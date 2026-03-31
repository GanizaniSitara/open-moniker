"use client";
import { useState, useMemo, useCallback } from "react";
import { Box, TextField, InputAdornment, Typography, Button } from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import FilterListIcon from "@mui/icons-material/FilterList";
import ApplicationCard from "./ApplicationCard";
import DatasetFilters from "./DatasetFilters";

interface ApplicationGridProps {
  applications: {
    appKey: string;
    displayName: string;
    description: string;
    color: string;
    category: string;
    status: string;
    owner: string;
    datasetCount: number;
    fieldCount: number;
  }[];
}

export default function ApplicationGrid({ applications }: ApplicationGridProps) {
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState<Record<string, Set<string>>>({
    Category: new Set(),
    Status: new Set(),
  });
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);

  // Step 1: filter by search text
  const searchFiltered = useMemo(() => {
    if (!search) return applications;
    const q = search.toLowerCase();
    return applications.filter(
      (a) =>
        a.displayName.toLowerCase().includes(q) ||
        a.description.toLowerCase().includes(q) ||
        a.owner.toLowerCase().includes(q) ||
        a.category.toLowerCase().includes(q)
    );
  }, [applications, search]);

  // Step 2: compute facet counts from search-filtered results
  const filterSections = useMemo(() => {
    const categoryCounts = new Map<string, number>();
    const statusCounts = new Map<string, number>();
    for (const a of searchFiltered) {
      const cat = a.category || "Other";
      categoryCounts.set(cat, (categoryCounts.get(cat) || 0) + 1);
      const st = a.status || "active";
      statusCounts.set(st, (statusCounts.get(st) || 0) + 1);
    }
    return [
      {
        label: "Category",
        options: [...categoryCounts.entries()]
          .sort((a, b) => b[1] - a[1])
          .map(([v, c]) => ({ value: v, label: v, count: c })),
      },
      {
        label: "Status",
        options: [...statusCounts.entries()]
          .sort((a, b) => b[1] - a[1])
          .map(([v, c]) => ({ value: v, label: v, count: c })),
      },
    ];
  }, [searchFiltered]);

  // Step 3: apply facet filters
  const displayed = useMemo(() => {
    let result = searchFiltered;
    if (filters.Category.size > 0) {
      result = result.filter((a) =>
        filters.Category.has(a.category || "Other")
      );
    }
    if (filters.Status.size > 0) {
      result = result.filter((a) =>
        filters.Status.has(a.status || "active")
      );
    }
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
    <Box sx={{ display: "flex", gap: 4 }}>
      <DatasetFilters
        sections={filterSections}
        selected={filters}
        onChange={handleFilterChange}
        mobileOpen={mobileFiltersOpen}
        onMobileToggle={() => setMobileFiltersOpen(false)}
        onClear={() => setFilters({ Category: new Set(), Status: new Set() })}
      />

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
        <TextField
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search applications..."
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
          {displayed.length} applications
        </Typography>
        {displayed.map((a) => (
          <ApplicationCard
            key={a.appKey}
            appKey={a.appKey}
            displayName={a.displayName}
            description={a.description}
            color={a.color}
            category={a.category}
            status={a.status}
            owner={a.owner}
            datasetCount={a.datasetCount}
            fieldCount={a.fieldCount}
          />
        ))}
      </Box>
    </Box>
  );
}
