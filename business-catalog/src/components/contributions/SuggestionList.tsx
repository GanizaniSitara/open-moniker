"use client";
import { useEffect, useState, useCallback } from "react";
import { Box, Typography, Chip } from "@mui/material";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import { fetchSuggestions } from "@/lib/contributions-client";
import type { Suggestion, SuggestionStatus } from "@/lib/contributions-types";

const STATUS_COLORS: Record<SuggestionStatus, "warning" | "success" | "error"> = {
  pending: "warning",
  approved: "success",
  rejected: "error",
};

interface SuggestionListProps {
  entityType: string;
  entityKey: string;
}

export default function SuggestionList({ entityType, entityKey }: SuggestionListProps) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);

  const load = useCallback(() => {
    fetchSuggestions(entityType, entityKey).then(setSuggestions).catch(() => {});
  }, [entityType, entityKey]);

  useEffect(() => { load(); }, [load]);

  if (suggestions.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
        No suggestions yet. Use &quot;Suggest an edit&quot; on the page to propose changes.
      </Typography>
    );
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
      {suggestions.map((s) => (
        <Box
          key={s.id}
          sx={{
            p: 1.5,
            borderRadius: 1,
            bgcolor: "#f8f9fa",
            border: "1px solid rgba(83,86,90,0.15)",
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
            <Typography variant="subtitle2" sx={{ fontSize: "0.8rem", color: "#022D5E" }}>
              {s.fieldName}
            </Typography>
            <Chip
              label={s.status}
              size="small"
              color={STATUS_COLORS[s.status as SuggestionStatus] || "default"}
              sx={{ fontSize: "0.7rem", height: 22 }}
            />
            <Box sx={{ flexGrow: 1 }} />
            <Typography variant="caption" color="text.secondary">
              {s.author} &middot; {new Date(s.createdAt).toLocaleDateString()}
            </Typography>
          </Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 0.5 }}>
            <Typography
              variant="body2"
              sx={{
                color: "#6B7280",
                textDecoration: "line-through",
                fontSize: "0.8rem",
                maxWidth: "40%",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {s.currentValue || "(empty)"}
            </Typography>
            <ArrowForwardIcon sx={{ fontSize: 14, color: "#9CA3AF" }} />
            <Typography
              variant="body2"
              sx={{
                color: "#022D5E",
                fontWeight: 500,
                fontSize: "0.8rem",
                maxWidth: "40%",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {s.proposedValue}
            </Typography>
          </Box>
          {s.reason && (
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: "block" }}>
              {s.reason}
            </Typography>
          )}
        </Box>
      ))}
    </Box>
  );
}
