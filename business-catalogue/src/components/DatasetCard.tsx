"use client";
import { Typography, Box } from "@mui/material";
import Link from "next/link";
interface Column {
  name: string;
  type: string;
}

interface DatasetCardProps {
  datasetKey: string;
  displayName: string;
  description?: string;
  sourceType?: string;
  domainDisplayName?: string;
  domainColor?: string;
  columnCount: number;
  classification?: string;
  isContainer: boolean;
  columns: Column[];
}

export default function DatasetCard({
  datasetKey,
  displayName,
  description,
  isContainer,
  columns,
}: DatasetCardProps) {
  return (
    <Link
      href={`/datasets/${datasetKey}`}
      style={{ textDecoration: "none", color: "inherit" }}
    >
      <Box
        sx={{
          py: 1.5,
          opacity: isContainer ? 0.6 : 1,
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
        {columns.length > 0 && (
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5, mt: 0.5 }}>
            {columns.map((col) => (
              <Box
                key={col.name}
                component="span"
                sx={{
                  fontSize: "0.75rem",
                  color: "#53565A",
                  bgcolor: "#f0f0f0",
                  px: 0.8,
                  py: 0.2,
                  borderRadius: 1,
                }}
              >
                {col.name}
              </Box>
            ))}
          </Box>
        )}
      </Box>
    </Link>
  );
}
