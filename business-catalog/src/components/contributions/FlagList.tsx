"use client";
import { Box, Typography, Chip } from "@mui/material";
import type { Flag } from "@/lib/contributions-types";

const FLAG_TYPE_COLORS: Record<string, { bg: string; color: string }> = {
  outdated: { bg: "#FFF3E0", color: "#E65100" },
  incorrect: { bg: "#FFEBEE", color: "#C62828" },
  missing: { bg: "#FFF8E1", color: "#F57F17" },
  unclear: { bg: "#E3F2FD", color: "#1565C0" },
};

const STATUS_COLORS: Record<string, "default" | "warning" | "success" | "info"> = {
  open: "warning",
  acknowledged: "info",
  resolved: "success",
  dismissed: "default",
};

interface FlagListProps {
  flags: Flag[];
}

export default function FlagList({ flags }: FlagListProps) {
  if (flags.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
        No flags reported yet.
      </Typography>
    );
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
      {flags.map((flag) => {
        const typeColor = FLAG_TYPE_COLORS[flag.flagType] || FLAG_TYPE_COLORS.unclear;
        return (
          <Box
            key={flag.id}
            sx={{
              p: 1.5,
              borderRadius: 1,
              bgcolor: "#f8f9fa",
              border: "1px solid rgba(83,86,90,0.15)",
            }}
          >
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
              <Chip
                label={flag.flagType}
                size="small"
                sx={{
                  bgcolor: typeColor.bg,
                  color: typeColor.color,
                  fontSize: "0.7rem",
                  height: 22,
                  fontWeight: 600,
                }}
              />
              <Chip
                label={flag.status}
                size="small"
                color={STATUS_COLORS[flag.status] || "default"}
                variant="outlined"
                sx={{ fontSize: "0.7rem", height: 22 }}
              />
              <Box sx={{ flexGrow: 1 }} />
              <Typography variant="caption" color="text.secondary">
                {flag.author} &middot; {new Date(flag.createdAt).toLocaleDateString()}
              </Typography>
            </Box>
            {flag.comment && (
              <Typography variant="body2" sx={{ color: "#53565A", mt: 0.5 }}>
                {flag.comment}
              </Typography>
            )}
          </Box>
        );
      })}
    </Box>
  );
}
