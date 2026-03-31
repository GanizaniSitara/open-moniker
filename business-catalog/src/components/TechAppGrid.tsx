"use client";
import { useState, useMemo, useCallback } from "react";
import { Box, TextField, InputAdornment, Typography, Button, Checkbox, FormControlLabel, Paper, Drawer } from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import FilterListIcon from "@mui/icons-material/FilterList";
import TechAppCard from "./TechAppCard";
import { TechnicalProfile } from "@/lib/tech-catalog-types";

interface TechApp {
  appKey: string;
  displayName: string;
  color: string;
  profile: TechnicalProfile;
}

interface TechAppGridProps {
  applications: TechApp[];
}

interface FilterSection {
  label: string;
  options: { value: string; label: string; count: number }[];
}

type Filters = Record<string, Set<string>>;

const FILTER_KEYS = ["Hosting", "Criticality", "Health"] as const;

function FilterPanel({
  sections,
  selected,
  onChange,
  onClear,
}: {
  sections: FilterSection[];
  selected: Filters;
  onChange: (section: string, value: string, checked: boolean) => void;
  onClear: () => void;
}) {
  const hasActive = Object.values(selected).some((s) => s.size > 0);
  return (
    <Box>
      {hasActive && (
        <Button size="small" onClick={onClear} sx={{ mb: 1 }}>
          Clear filters
        </Button>
      )}
      {sections.map((section) => (
        <Box key={section.label} sx={{ mb: 2 }}>
          <Typography variant="caption" sx={{ fontWeight: 700, textTransform: "uppercase", color: "#53565A" }}>
            {section.label}
          </Typography>
          {section.options.map((opt) => (
            <FormControlLabel
              key={opt.value}
              sx={{ display: "flex", mx: 0 }}
              control={
                <Checkbox
                  size="small"
                  checked={selected[section.label]?.has(opt.value) ?? false}
                  onChange={(_, checked) => onChange(section.label, opt.value, checked)}
                />
              }
              label={
                <Typography variant="body2" sx={{ fontSize: "0.85rem" }}>
                  {opt.label} ({opt.count})
                </Typography>
              }
            />
          ))}
        </Box>
      ))}
    </Box>
  );
}

export default function TechAppGrid({ applications }: TechAppGridProps) {
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState<Filters>({
    Hosting: new Set(),
    Criticality: new Set(),
    Health: new Set(),
  });
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);

  // Step 1: filter by search text
  const searchFiltered = useMemo(() => {
    if (!search) return applications;
    const q = search.toLowerCase();
    return applications.filter(
      (a) =>
        a.displayName.toLowerCase().includes(q) ||
        a.appKey.toLowerCase().includes(q) ||
        a.profile.infrastructure.hosting.toLowerCase().includes(q) ||
        a.profile.cmdb.ci_id.toLowerCase().includes(q)
    );
  }, [applications, search]);

  // Step 2: compute facet counts
  const filterSections = useMemo<FilterSection[]>(() => {
    const hosting = new Map<string, number>();
    const criticality = new Map<string, number>();
    const health = new Map<string, number>();
    for (const a of searchFiltered) {
      const h = a.profile.infrastructure.hosting;
      hosting.set(h, (hosting.get(h) || 0) + 1);
      const c = a.profile.cmdb.business_criticality;
      criticality.set(c, (criticality.get(c) || 0) + 1);
      const s = a.profile.sla.health_status;
      health.set(s, (health.get(s) || 0) + 1);
    }
    return [
      {
        label: "Hosting",
        options: [...hosting.entries()]
          .sort((a, b) => b[1] - a[1])
          .map(([v, c]) => ({ value: v, label: v, count: c })),
      },
      {
        label: "Criticality",
        options: [...criticality.entries()]
          .sort()
          .map(([v, c]) => ({ value: v, label: v, count: c })),
      },
      {
        label: "Health",
        options: [...health.entries()]
          .sort((a, b) => b[1] - a[1])
          .map(([v, c]) => ({ value: v, label: v, count: c })),
      },
    ];
  }, [searchFiltered]);

  // Step 3: apply facet filters
  const displayed = useMemo(() => {
    let result = searchFiltered;
    if (filters.Hosting.size > 0) {
      result = result.filter((a) => filters.Hosting.has(a.profile.infrastructure.hosting));
    }
    if (filters.Criticality.size > 0) {
      result = result.filter((a) => filters.Criticality.has(a.profile.cmdb.business_criticality));
    }
    if (filters.Health.size > 0) {
      result = result.filter((a) => filters.Health.has(a.profile.sla.health_status));
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

  const clearFilters = useCallback(() => {
    setFilters({ Hosting: new Set(), Criticality: new Set(), Health: new Set() });
  }, []);

  const filterPanel = (
    <FilterPanel
      sections={filterSections}
      selected={filters}
      onChange={handleFilterChange}
      onClear={clearFilters}
    />
  );

  return (
    <Box sx={{ display: "flex", gap: 4 }}>
      {/* Desktop sidebar */}
      <Box sx={{ width: 220, flexShrink: 0, display: { xs: "none", md: "block" } }}>
        {filterPanel}
      </Box>

      {/* Mobile drawer */}
      <Drawer
        anchor="left"
        open={mobileFiltersOpen}
        onClose={() => setMobileFiltersOpen(false)}
        sx={{ display: { md: "none" } }}
      >
        <Box sx={{ p: 2, width: 260 }}>{filterPanel}</Box>
      </Drawer>

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
          placeholder="Search by app name, hosting, CI ID..."
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
          <TechAppCard
            key={a.appKey}
            appKey={a.appKey}
            displayName={a.displayName}
            color={a.color}
            profile={a.profile}
          />
        ))}
      </Box>
    </Box>
  );
}
