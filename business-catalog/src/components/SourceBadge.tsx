"use client";
import { Box } from "@mui/material";

export default function SourceBadge({ type }: { type: string }) {
  return (
    <Box
      component="span"
      sx={{
        display: "inline-block",
        bgcolor: "rgba(83,86,90,0.12)",
        color: "#53565A",
        fontSize: "0.65rem",
        fontWeight: 600,
        px: 0.8,
        py: 0.2,
        borderRadius: "4px",
        lineHeight: 1.3,
        textTransform: "uppercase",
        letterSpacing: "0.03em",
      }}
    >
      {type}
    </Box>
  );
}
