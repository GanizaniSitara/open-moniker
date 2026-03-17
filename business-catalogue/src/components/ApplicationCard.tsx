"use client";
import { Typography, Box, Chip } from "@mui/material";
import Link from "next/link";

interface ApplicationCardProps {
  appKey: string;
  displayName: string;
  description: string;
  color: string;
  category: string;
  status: string;
  owner: string;
  datasetCount: number;
  fieldCount: number;
}

export default function ApplicationCard({
  appKey,
  displayName,
  description,
  color,
  category,
  status,
  owner,
  datasetCount,
  fieldCount,
}: ApplicationCardProps) {
  return (
    <Link
      href={`/applications/${appKey}`}
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
            <Box sx={{ display: "flex", gap: 0.5, flexShrink: 0 }}>
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
                  }}
                />
              )}
              {fieldCount > 0 && (
                <Chip
                  label={`${fieldCount} fields`}
                  size="small"
                  sx={{
                    bgcolor: "#789D4A",
                    color: "white",
                    fontWeight: 600,
                    fontSize: "0.7rem",
                    height: 22,
                  }}
                />
              )}
            </Box>
          </Box>
          {description && (
            <Typography
              variant="body2"
              sx={{ color: "#53565A", lineHeight: 1.5 }}
            >
              {description}
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
            {category && (
              <Chip
                label={category}
                size="small"
                variant="outlined"
                sx={{ fontSize: "0.7rem" }}
              />
            )}
            <Chip
              label={status}
              size="small"
              color={
                status === "active"
                  ? "success"
                  : status === "decommissioned"
                    ? "error"
                    : "info"
              }
              sx={{ fontSize: "0.7rem" }}
            />
          </Box>
        </Box>
      </Box>
    </Link>
  );
}
