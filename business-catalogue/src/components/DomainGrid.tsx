"use client";
import { useState, useMemo, useCallback } from "react";
import { Box, TextField, InputAdornment, Typography } from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import DomainCard from "./DomainCard";
import DatasetFilters from "./DatasetFilters";

interface DomainGridProps {
  domains: {
    domainKey: string;
    displayName: string;
    notes: string;
    color: string;
    dataCategory: string;
    datasetCount: number;
    confidentiality: string;
    owner: string;
  }[];
}

export default function DomainGrid({ domains }: DomainGridProps) {
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState<Record<string, Set<string>>>({
    Category: new Set(),
  });

  // Step 1: filter by search text
  const searchFiltered = useMemo(() => {
    if (!search) return domains;
    const q = search.toLowerCase();
    return domains.filter(
      (d) =>
        d.displayName.toLowerCase().includes(q) ||
        d.notes.toLowerCase().includes(q) ||
        d.owner.toLowerCase().includes(q)
    );
  }, [domains, search]);

  // Step 2: compute facet counts from search-filtered results
  const filterSections = useMemo(() => {
    const categoryCounts = new Map<string, number>();
    for (const d of searchFiltered) {
      const cat = d.dataCategory || "Other";
      categoryCounts.set(cat, (categoryCounts.get(cat) || 0) + 1);
    }
    return [
      {
        label: "Category",
        options: [...categoryCounts.entries()]
          .sort((a, b) => b[1] - a[1])
          .map(([v, c]) => ({ value: v, label: v, count: c })),
      },
    ];
  }, [searchFiltered]);

  // Step 3: apply facet filters
  const displayed = useMemo(() => {
    let result = searchFiltered;
    if (filters.Category.size > 0) {
      result = result.filter((d) =>
        filters.Category.has(d.dataCategory || "Other")
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
        onClear={() => setFilters({ Category: new Set() })}
      />

      <Box sx={{ flexGrow: 1, minWidth: 0 }}>
        <TextField
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search domains..."
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
          {displayed.length} domains
        </Typography>
        {displayed.map((d) => (
          <DomainCard
            key={d.domainKey}
            domainKey={d.domainKey}
            displayName={d.displayName}
            color={d.color}
            notes={d.notes}
            dataCategory={d.dataCategory}
            confidentiality={d.confidentiality}
            owner={d.owner}
            datasetCount={d.datasetCount}
          />
        ))}
      </Box>
    </Box>
  );
}
