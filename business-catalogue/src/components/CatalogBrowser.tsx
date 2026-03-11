"use client";
import { useState, useMemo, useCallback, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import {
  Container,
  Typography,
  Box,
  TextField,
  InputAdornment,
  Chip,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import DatasetCard from "@/components/DatasetCard";
import DatasetFilters from "@/components/DatasetFilters";
import type { Vendor } from "@/lib/vendors";
interface BrowseDataset {
  key: string;
  display_name: string;
  description?: string;
  domainDisplayName?: string;
  domainColor?: string;
  isContainer: boolean;
  classification?: string;
  vendor?: string;
  source_binding?: { type: string };
  schema: null;
}

export default function CatalogBrowser() {
  const searchParams = useSearchParams();
  const vendorParam = searchParams.get("vendor");
  const [searchQuery, setSearchQuery] = useState("");
  const [datasets, setDatasets] = useState<BrowseDataset[]>([]);
  const [, setDomains] = useState<{ key: string; display_name: string; color: string }[]>([]);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [filters, setFilters] = useState<Record<string, Set<string>>>({
    Domain: new Set(),
  });

  useEffect(() => {
    Promise.all([
      fetch("/api/search?q=&all=datasets").then((r) => r.json()),
      fetch("/api/vendors").then((r) => r.json()),
    ]).then(([d, v]) => {
      setDatasets(d.datasets || []);
      setDomains(d.domains || []);
      setVendors(v.vendors || []);
      setLoaded(true);
    });
  }, []);

  const vendorName = vendorParam
    ? vendors.find((v) => v.key === vendorParam)?.name || vendorParam
    : null;

  // Step 1: filter by search text and vendor param
  const searchFiltered = useMemo(() => {
    let result = datasets.filter((ds) => !ds.isContainer);
    if (vendorParam) {
      result = result.filter((ds) => ds.vendor === vendorParam);
    }
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
  }, [datasets, searchQuery, vendorParam]);

  // Step 2: compute facet counts from search-filtered results
  const filterSections = useMemo(() => {
    const categoryCounts = new Map<string, number>();

    for (const ds of searchFiltered) {
      const cat = ds.domainDisplayName || "Other";
      categoryCounts.set(cat, (categoryCounts.get(cat) || 0) + 1);
    }

    return [
      {
        label: "Domain",
        options: [...categoryCounts.entries()]
          .sort((a, b) => b[1] - a[1])
          .map(([v, c]) => ({ value: v, label: v, count: c })),
      },
    ];
  }, [searchFiltered]);

  // Step 3: apply facet filters to search-filtered results
  const displayedDatasets = useMemo(() => {
    let result = searchFiltered;

    if (filters.Domain.size > 0) {
      result = result.filter((ds) =>
        filters.Domain.has(ds.domainDisplayName || "Other")
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
              Domain: new Set(),
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

          {vendorName && (
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}>
              <Typography variant="body2" color="text.secondary">
                Filtered by vendor:
              </Typography>
              <Chip
                label={vendorName}
                size="small"
                onDelete={() => {
                  window.history.replaceState(null, "", "/datasets");
                  window.location.reload();
                }}
                sx={{ fontWeight: 600 }}
              />
            </Box>
          )}

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
              vendor={ds.vendor}
              columnCount={0}
              classification={ds.classification}
              isContainer={ds.isContainer}
              columns={[]}
            />
          ))}
        </Box>
      </Box>
    </Container>
  );
}
