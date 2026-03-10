"use client";
import { Typography, Box, Chip } from "@mui/material";
import Link from "next/link";

interface FieldCardProps {
  fieldKey: string;
  displayName: string;
  description?: string;
  formula?: string;
  unit?: string;
  datasetCount: number;
  semanticTags?: string[];
}

export default function FieldCard({
  fieldKey,
  displayName,
  description,
  formula,
  unit,
  datasetCount,
  semanticTags,
}: FieldCardProps) {
  return (
    <Link
      href={`/fields/${fieldKey}`}
      style={{ textDecoration: "none", color: "inherit" }}
    >
      <Box
        sx={{
          py: 1.5,
          "&:hover h6": { textDecoration: "underline" },
        }}
      >
        <Typography
          variant="h6"
          sx={{
            color: "#005587",
            fontWeight: 600,
            fontSize: "1rem",
            lineHeight: 1.3,
            mb: 0.3,
          }}
        >
          {displayName}
        </Typography>
        {description && (
          <Typography
            variant="body2"
            sx={{
              color: "#53565A",
              lineHeight: 1.5,
            }}
          >
            {description}
          </Typography>
        )}
        {formula && (
          <Typography
            variant="body2"
            sx={{
              fontFamily: "monospace",
              bgcolor: "#f8f9fa",
              px: 1,
              py: 0.5,
              borderRadius: "4px",
              mt: 0.5,
              display: "inline-block",
              fontSize: "0.8rem",
            }}
          >
            {formula}
          </Typography>
        )}
        <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap", mt: 0.5 }}>
          {unit && (
            <Chip
              label={unit}
              size="small"
              variant="outlined"
              sx={{ fontSize: "0.7rem" }}
            />
          )}
          {datasetCount > 0 && (
            <Chip
              label={`${datasetCount} datasets`}
              size="small"
              sx={{
                bgcolor: "#789D4A",
                color: "white",
                fontSize: "0.7rem",
              }}
            />
          )}
          {semanticTags?.map((tag) => (
            <Chip
              key={tag}
              label={tag}
              size="small"
              variant="outlined"
              sx={{ fontSize: "0.65rem" }}
            />
          ))}
        </Box>
      </Box>
    </Link>
  );
}
