"use client";
import { Typography, Box, Chip } from "@mui/material";

interface VendorCardProps {
  name: string;
  description: string;
  category: string;
  datasetCount: number;
  website?: string;
}

export default function VendorCard({
  name,
  description,
  category,
  datasetCount,
  website,
}: VendorCardProps) {
  return (
    <Box
      sx={{
        display: "flex",
        gap: 2.5,
        py: 2,
        borderBottom: "1px solid rgba(0,0,0,0.08)",
        "&:last-child": { borderBottom: "none" },
      }}
    >
      {/* Dataset count badge */}
      <Box
        sx={{
          width: 56,
          height: 56,
          borderRadius: "8px",
          bgcolor: "#022D5E",
          color: "white",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
          mt: 0.3,
        }}
      >
        <Typography sx={{ fontWeight: 700, fontSize: "1.25rem" }}>
          {datasetCount}
        </Typography>
      </Box>

      <Box sx={{ minWidth: 0 }}>
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
          {website ? (
            <a
              href={website}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "inherit", textDecoration: "none" }}
              onMouseOver={(e) =>
                (e.currentTarget.style.textDecoration = "underline")
              }
              onMouseOut={(e) =>
                (e.currentTarget.style.textDecoration = "none")
              }
            >
              {name}
            </a>
          ) : (
            name
          )}
        </Typography>
        <Typography
          variant="body2"
          sx={{ color: "#53565A", lineHeight: 1.5, mb: 0.5 }}
        >
          {description}
        </Typography>
        <Chip
          label={category}
          size="small"
          variant="outlined"
          sx={{ fontSize: "0.7rem" }}
        />
      </Box>
    </Box>
  );
}
