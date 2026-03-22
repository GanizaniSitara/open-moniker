"use client";
import { Typography, Box, Paper, Chip } from "@mui/material";
import { DiagramRef } from "@/lib/tech-catalogue-types";

interface Props {
  diagrams: DiagramRef[];
}

const typeColor: Record<string, string> = {
  architecture: "#022D5E",
  sequence: "#8E44AD",
  deployment: "#E74C3C",
  "data-flow": "#1ABC9C",
};

export default function DiagramSection({ diagrams }: Props) {
  if (diagrams.length === 0) return null;

  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h5" sx={{ mb: 1.5, color: "#022D5E" }}>
        Architecture Diagrams
      </Typography>
      <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
        {diagrams.map((d) => (
          <Paper key={d.file} variant="outlined" sx={{ p: 2, minWidth: 220, flex: 1 }}>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
              {d.name}
            </Typography>
            <Chip
              label={d.type}
              size="small"
              sx={{
                bgcolor: typeColor[d.type] || "#53565A",
                color: "white",
                fontSize: "0.7rem",
                height: 20,
                mb: 0.5,
              }}
            />
            <Typography variant="caption" sx={{ display: "block", color: "#53565A", fontFamily: "monospace" }}>
              {d.file}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Updated: {d.last_updated}
            </Typography>
          </Paper>
        ))}
      </Box>
    </Box>
  );
}
