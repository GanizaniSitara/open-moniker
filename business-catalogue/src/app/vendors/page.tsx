"use client";
import { useState, useMemo, useCallback, useEffect } from "react";
import {
  Container,
  Box,
  TextField,
  InputAdornment,
  Typography,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import PageTitle from "@/components/PageTitle";
import DatasetFilters from "@/components/DatasetFilters";
import VendorCard from "@/components/VendorCard";
import type { Vendor } from "@/lib/vendors";

export default function VendorsPage() {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState<Record<string, Set<string>>>({
    Category: new Set(),
  });

  useEffect(() => {
    fetch("/api/vendors")
      .then((r) => r.json())
      .then((d) => setVendors(d.vendors || []));
  }, []);

  const searchFiltered = useMemo(() => {
    if (!search) return vendors;
    const q = search.toLowerCase();
    return vendors.filter(
      (v) =>
        v.name.toLowerCase().includes(q) ||
        v.description.toLowerCase().includes(q)
    );
  }, [search, vendors]);

  const filterSections = useMemo(() => {
    const categoryCounts = new Map<string, number>();
    for (const v of searchFiltered) {
      categoryCounts.set(v.category, (categoryCounts.get(v.category) || 0) + 1);
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

  const displayed = useMemo(() => {
    let result = searchFiltered;
    if (filters.Category.size > 0) {
      result = result.filter((v) => filters.Category.has(v.category));
    }
    return result.sort((a, b) => a.name.localeCompare(b.name));
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
    <>
      <PageTitle title="Vendors" />
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Box sx={{ display: "flex", gap: 4 }}>
          <DatasetFilters
            sections={filterSections}
            selected={filters}
            onChange={handleFilterChange}
            onClear={() => setFilters({ Category: new Set() })}
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

          <Box sx={{ flexGrow: 1, minWidth: 0 }}>
            <TextField
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search vendors..."
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
              {displayed.length} vendors
            </Typography>

            {displayed.map((v) => (
              <VendorCard
                key={v.key}
                vendorKey={v.key}
                name={v.name}
                description={v.description}
                category={v.category}
                datasetCount={v.datasetCount}
                website={v.website}
              />
            ))}
          </Box>
        </Box>
      </Container>
    </>
  );
}
