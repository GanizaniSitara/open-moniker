"use client";
import { Typography, Box, Chip } from "@mui/material";
import Link from "next/link";

interface DomainCardProps {
  domainKey: string;
  displayName: string;
  color: string;
  notes: string;
  dataCategory: string;
  confidentiality: string;
  owner: string;
  datasetCount: number;
}

export default function DomainCard({
  domainKey,
  displayName,
  color,
  notes,
  dataCategory,
  confidentiality,
  owner,
  datasetCount,
}: DomainCardProps) {
  return (
    <Link
      href={`/domains/${domainKey}`}
      style={{ textDecoration: "none", color: "inherit" }}
    >
      <Box
        sx={{
          border: "1px solid rgba(0,0,0,0.1)",
          borderRadius: "8px",
          overflow: "hidden",
          transition: "box-shadow 0.15s, transform 0.15s",
          "&:hover": {
            boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
            transform: "translateY(-1px)",
          },
          height: "100%",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* Top color bar */}
        <Box sx={{ height: 4, bgcolor: color }} />

        <Box sx={{ p: 2, flexGrow: 1, display: "flex", flexDirection: "column" }}>
          {/* Header: icon + name */}
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
            <Box
              sx={{
                width: 28,
                height: 28,
                borderRadius: "6px",
                bgcolor: color,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="7" height="7" rx="1" />
                <rect x="14" y="3" width="7" height="7" rx="1" />
                <rect x="3" y="14" width="7" height="7" rx="1" />
                <rect x="14" y="14" width="7" height="7" rx="1" />
              </svg>
            </Box>
            <Typography
              variant="h6"
              sx={{
                color: "#005587",
                fontWeight: 600,
                fontSize: "0.95rem",
                lineHeight: 1.3,
                flexGrow: 1,
              }}
            >
              {displayName}
            </Typography>
            <Chip
              label={confidentiality}
              size="small"
              color={confidentiality === "confidential" ? "warning" : "default"}
              sx={{ fontSize: "0.65rem", height: 20 }}
            />
          </Box>

          {/* Notes */}
          {notes && (
            <Typography
              variant="body2"
              sx={{
                color: "#53565A",
                lineHeight: 1.5,
                fontSize: "0.82rem",
                mb: 1,
                flexGrow: 1,
              }}
            >
              {notes}
            </Typography>
          )}

          {/* Category + owner */}
          <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap", mb: 1 }}>
            <Chip
              label={dataCategory}
              size="small"
              sx={{
                fontSize: "0.65rem",
                height: 20,
                bgcolor: `${color}18`,
                color: color,
                fontWeight: 600,
                border: `1px solid ${color}40`,
              }}
            />
            {owner && (
              <Chip
                label={owner}
                size="small"
                variant="outlined"
                sx={{ fontSize: "0.65rem", height: 20 }}
              />
            )}
          </Box>

          {/* Count bar */}
          <Box
            sx={{
              pt: 1,
              borderTop: "1px solid rgba(0,0,0,0.06)",
            }}
          >
            <Typography variant="caption" sx={{ color: "#53565A" }}>
              <strong>{datasetCount}</strong> datasets
            </Typography>
          </Box>
        </Box>
      </Box>
    </Link>
  );
}
