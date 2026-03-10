"use client";
import { useState } from "react";
import { Box, Typography, Button } from "@mui/material";

interface FilterSection {
  label: string;
  options: { value: string; label: string; count: number }[];
}

interface DatasetFiltersProps {
  sections: FilterSection[];
  selected: Record<string, Set<string>>;
  onChange: (sectionLabel: string, value: string, checked: boolean) => void;
  onClear: () => void;
}

const COLLAPSED_LIMIT = 5;

export default function DatasetFilters({
  sections,
  selected,
  onChange,
  onClear,
}: DatasetFiltersProps) {
  const hasAny = Object.values(selected).some((s) => s.size > 0);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  return (
    <Box sx={{ width: 220, flexShrink: 0 }}>
      {hasAny && (
        <Button
          size="small"
          onClick={onClear}
          sx={{ textTransform: "none", color: "#005587", mb: 1 }}
        >
          Clear filters
        </Button>
      )}
      {sections.map((section, i) => {
        const isExpanded = expanded[section.label] || false;
        const visibleOptions = isExpanded
          ? section.options
          : section.options.slice(0, COLLAPSED_LIMIT);
        const hasMore = section.options.length > COLLAPSED_LIMIT;

        return (
          <Box key={section.label} sx={{ mb: i < sections.length - 1 ? 2 : 0 }}>
            <Typography
              variant="subtitle2"
              sx={{
                mb: 0.5,
                color: "#000",
                fontWeight: 700,
              }}
            >
              {section.label}
            </Typography>
            {visibleOptions.map((opt) => {
              const active = selected[section.label]?.has(opt.value) || false;
              return (
                <Typography
                  key={opt.value}
                  variant="body2"
                  onClick={() => onChange(section.label, opt.value, !active)}
                  sx={{
                    py: 0.2,
                    cursor: "pointer",
                    color: active ? "#005587" : "#005587",
                    fontWeight: active ? 700 : 400,
                    "&:hover": { textDecoration: "underline" },
                  }}
                >
                  <Box
                    component="span"
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      width: "100%",
                    }}
                  >
                    <span>{opt.label}</span>
                    <span style={{ color: "#999", fontWeight: 400 }}>
                      ({opt.count})
                    </span>
                  </Box>
                </Typography>
              );
            })}
            {hasMore && (
              <Typography
                variant="caption"
                onClick={() =>
                  setExpanded((prev) => ({
                    ...prev,
                    [section.label]: !isExpanded,
                  }))
                }
                sx={{
                  color: "#53565A",
                  cursor: "pointer",
                  display: "block",
                  mt: 0.3,
                  "&:hover": { textDecoration: "underline" },
                }}
              >
                {isExpanded
                  ? "Show less"
                  : `Show ${section.options.length - COLLAPSED_LIMIT} more`}
              </Typography>
            )}
          </Box>
        );
      })}
    </Box>
  );
}
