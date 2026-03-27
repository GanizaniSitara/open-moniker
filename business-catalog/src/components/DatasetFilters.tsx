"use client";
import { useState } from "react";
import {
  Box,
  Typography,
  Button,
  Checkbox,
  FormControlLabel,
  Drawer,
} from "@mui/material";

interface FilterSection {
  label: string;
  options: { value: string; label: string; count: number }[];
}

interface DatasetFiltersProps {
  sections: FilterSection[];
  selected: Record<string, Set<string>>;
  onChange: (sectionLabel: string, value: string, checked: boolean) => void;
  onClear: () => void;
  onSelectAll?: (sectionLabel: string) => void;
  mobileOpen?: boolean;
  onMobileToggle?: () => void;
}

const COLLAPSED_LIMIT = 25;

export default function DatasetFilters({
  sections,
  selected,
  onChange,
  onClear,
  onSelectAll,
  mobileOpen,
  onMobileToggle,
}: DatasetFiltersProps) {
  const hasAny = Object.values(selected).some((s) => s.size > 0);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const filtersContent = sections.map((section, i) => {
    const isExpanded = expanded[section.label] || false;
    const visibleOptions = isExpanded
      ? section.options
      : section.options.slice(0, COLLAPSED_LIMIT);
    const hasMore = section.options.length > COLLAPSED_LIMIT;
    const selectedSet = selected[section.label] || new Set();
    const allSelected =
      section.options.length > 0 &&
      section.options.every((opt) => selectedSet.has(opt.value));

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

        {/* Clear All */}
        {section.options.length > 1 && (
          <Box sx={{ display: "flex", gap: 0.5, mb: 0.5 }}>
            <Button
              size="small"
              disabled={selectedSet.size === 0}
              onClick={onClear}
              sx={{
                textTransform: "none",
                color: "#005587",
                fontSize: "0.7rem",
                minWidth: 0,
                p: "1px 4px",
              }}
            >
              Clear all
            </Button>
          </Box>
        )}

        {visibleOptions.map((opt) => {
          const active = selectedSet.has(opt.value);
          return (
            <FormControlLabel
              key={opt.value}
              control={
                <Checkbox
                  checked={active}
                  onChange={(_, checked) =>
                    onChange(section.label, opt.value, checked)
                  }
                  size="small"
                  sx={{
                    p: "2px 4px 2px 0",
                    color: "#005587",
                    "&.Mui-checked": { color: "#005587" },
                  }}
                />
              }
              label={
                <Box
                  component="span"
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    width: "100%",
                    fontSize: "0.85rem",
                    color: "#005587",
                    fontWeight: active ? 700 : 400,
                  }}
                >
                  <span>{opt.label}</span>
                  <span style={{ color: "#999", fontWeight: 400, marginLeft: 8 }}>
                    ({opt.count})
                  </span>
                </Box>
              }
              sx={{
                ml: 0,
                mr: 0,
                width: "100%",
                "& .MuiFormControlLabel-label": { width: "100%" },
              }}
            />
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
  });

  return (
    <>
      <Box sx={{ width: 220, flexShrink: 0, display: { xs: "none", md: "block" } }}>
        {filtersContent}
      </Box>
      {onMobileToggle && (
        <Drawer anchor="left" open={!!mobileOpen} onClose={onMobileToggle}>
          <Box sx={{ width: 260, p: 2 }}>{filtersContent}</Box>
        </Drawer>
      )}
    </>
  );
}
