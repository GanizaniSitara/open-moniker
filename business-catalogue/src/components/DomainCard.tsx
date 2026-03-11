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
          py: 1.5,
          display: "flex",
          alignItems: "flex-start",
          gap: 2,
          "&:hover h6": { textDecoration: "underline" },
        }}
      >
        {/* Color bar */}
        <Box
          sx={{
            width: 4,
            minHeight: 40,
            alignSelf: "stretch",
            bgcolor: color,
            borderRadius: 1,
            flexShrink: 0,
            mt: 0.3,
          }}
        />

        <Box sx={{ flexGrow: 1, minWidth: 0 }}>
          <Box sx={{ display: "flex", alignItems: "center", mb: 0.3 }}>
            <Typography
              variant="h6"
              sx={{
                color: "#005587",
                fontWeight: 600,
                fontSize: "1rem",
                lineHeight: 1.3,
              }}
            >
              {displayName}
            </Typography>
            <Box sx={{ flexGrow: 1 }} />
            {datasetCount > 0 && (
              <Chip
                label={`${datasetCount} datasets`}
                size="small"
                sx={{
                  bgcolor: "#022D5E",
                  color: "white",
                  fontWeight: 600,
                  fontSize: "0.7rem",
                  height: 22,
                  flexShrink: 0,
                }}
              />
            )}
          </Box>
          {notes && (
            <Typography
              variant="body2"
              sx={{ color: "#53565A", lineHeight: 1.5 }}
            >
              {notes}
            </Typography>
          )}
          <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap", mt: 0.5 }}>
            {owner && (
              <Chip
                label={owner}
                size="small"
                variant="outlined"
                sx={{ fontSize: "0.7rem" }}
              />
            )}
            <Chip
              label={dataCategory}
              size="small"
              variant="outlined"
              sx={{ fontSize: "0.7rem" }}
            />
            <Chip
              label={confidentiality}
              size="small"
              variant="outlined"
              color={confidentiality === "confidential" ? "warning" : "default"}
              sx={{ fontSize: "0.7rem" }}
            />
          </Box>
        </Box>
      </Box>
    </Link>
  );
}
