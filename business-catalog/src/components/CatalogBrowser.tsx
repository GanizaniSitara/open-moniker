"use client";
import { useState, useMemo, useCallback, useEffect, useRef } from "react";
import { useSearchParams } from "next/navigation";

const PAGE_SIZE = 50;
import {
  Container,
  Typography,
  Box,
  TextField,
  InputAdornment,
  Chip,
  Button,
  Skeleton,
  LinearProgress,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import FilterListIcon from "@mui/icons-material/FilterList";
import DatasetCard from "@/components/DatasetCard";
import DatasetFilters from "@/components/DatasetFilters";
import { fetchCached } from "@/lib/data-cache";
import type { Vendor } from "@/lib/vendors";
import type { BrowseDataset, BrowseDomain } from "@/lib/load-datasets";

interface CatalogBrowserProps {
  initialDatasets?: BrowseDataset[];
  initialDomains?: BrowseDomain[];
  totalHint?: number;
}

export default function CatalogBrowser({
  initialDatasets,
  initialDomains,
  totalHint,
}: CatalogBrowserProps) {
  const searchParams = useSearchParams();
  const vendorParam = searchParams.get("vendor");
  const [searchQuery, setSearchQuery] = useState("");
  const [datasets, setDatasets] = useState<BrowseDataset[]>(initialDatasets || []);
  const [, setDomains] = useState<BrowseDomain[]>(initialDomains || []);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const hasInitial = !!initialDatasets && initialDatasets.length > 0;
  const [fullyLoaded, setFullyLoaded] = useState(false);
  const [filters, setFilters] = useState<Record<string, Set<string>>>({
    Domain: new Set(),
    Maturity: new Set(),
  });
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);

  // Fetch full catalog in background
  useEffect(() => {
    Promise.all([
      fetchCached("/api/search?q=&all=datasets"),
      fetchCached("/api/vendors"),
    ]).then(([d, v]) => {
      setDatasets(d.datasets || []);
      setDomains(d.domains || []);
      setVendors(v.vendors || []);
      setFullyLoaded(true);
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
    const maturityCounts = new Map<string, number>();

    for (const ds of searchFiltered) {
      const cat = ds.domainDisplayName || "Other";
      categoryCounts.set(cat, (categoryCounts.get(cat) || 0) + 1);
      const m = ds.maturity || "bronze";
      maturityCounts.set(m, (maturityCounts.get(m) || 0) + 1);
    }

    return [
      {
        label: "Domain",
        options: [...categoryCounts.entries()]
          .sort((a, b) => b[1] - a[1])
          .map(([v, c]) => ({ value: v, label: v, count: c })),
      },
      {
        label: "Maturity",
        options: [...maturityCounts.entries()]
          .sort((a, b) => b[1] - a[1])
          .map(([v, c]) => ({ value: v, label: v === "gold" ? "Gold" : v === "silver" ? "Silver" : "Bronze", count: c })),
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
    if (filters.Maturity.size > 0) {
      result = result.filter((ds) =>
        filters.Maturity.has(ds.maturity || "bronze")
      );
    }
    result.sort((a, b) => a.display_name.localeCompare(b.display_name));
    return result;
  }, [searchFiltered, filters]);

  // Progressive rendering: show PAGE_SIZE initially, load more on scroll
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);
  const sentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setVisibleCount(PAGE_SIZE);
  }, [searchQuery, filters, vendorParam]);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setVisibleCount((prev) => prev + PAGE_SIZE);
        }
      },
      { rootMargin: "200px" }
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [displayedDatasets]);

  const visibleDatasets = useMemo(
    () => displayedDatasets.slice(0, visibleCount),
    [displayedDatasets, visibleCount]
  );

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

  const showSkeleton = !hasInitial && !fullyLoaded;

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Box sx={{ display: "flex", gap: 4 }}>
        {/* Sidebar */}
        <DatasetFilters
          sections={filterSections}
          selected={filters}
          onChange={handleFilterChange}
          mobileOpen={mobileFiltersOpen}
          onMobileToggle={() => setMobileFiltersOpen(false)}
          onClear={() =>
            setFilters({
              Domain: new Set(),
              Maturity: new Set(),
            })
          }
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

        {/* Dataset cards */}
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

          <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
            {fullyLoaded
              ? `${displayedDatasets.length} datasets`
              : hasInitial
                ? `${displayedDatasets.length} datasets shown`
                : "Loading catalog\u2026"}
          </Typography>
          {hasInitial && !fullyLoaded && (
            <Box sx={{ mb: 1.5 }}>
              <LinearProgress
                sx={{ height: 2, borderRadius: 1, bgcolor: "#e0e0e0", "& .MuiLinearProgress-bar": { bgcolor: "#005587" } }}
              />
            </Box>
          )}
          {!hasInitial && fullyLoaded && (
            <Box sx={{ mb: 1.5 }} />
          )}

          {showSkeleton && (
            <>
              {Array.from({ length: 12 }, (_, i) => (
                <Box key={i} sx={{ py: 1.5 }}>
                  <Box sx={{ display: "flex", alignItems: "center", mb: 0.3 }}>
                    <Skeleton variant="text" width={180 + (i % 3) * 60} height={28} />
                    <Box sx={{ flexGrow: 1 }} />
                    <Skeleton variant="rounded" width={70} height={22} sx={{ borderRadius: "16px", mr: 0.5 }} />
                    <Skeleton variant="rounded" width={55} height={22} sx={{ borderRadius: "16px" }} />
                  </Box>
                  <Skeleton variant="text" width="85%" height={20} />
                </Box>
              ))}
            </>
          )}

          {visibleDatasets.map((ds) => (
            <DatasetCard
              key={ds.key}
              datasetKey={ds.key}
              displayName={ds.display_name}
              description={ds.description}
              sourceType={ds.source_binding?.type}
              domainDisplayName={ds.domainDisplayName}
              domainColor={ds.domainColor}
              vendor={ds.vendor}
              maturity={ds.maturity}
              columnCount={0}
              classification={ds.classification}
              isContainer={ds.isContainer}
              columns={[]}
            />
          ))}
          {visibleCount < displayedDatasets.length && (
            <div ref={sentinelRef} style={{ height: 1 }} />
          )}
        </Box>
      </Box>
    </Container>
  );
}
