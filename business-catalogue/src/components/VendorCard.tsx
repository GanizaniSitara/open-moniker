"use client";
import { useState } from "react";
import { Typography, Box, Chip } from "@mui/material";
import Image from "next/image";
import Link from "next/link";

const SVG_VENDORS = new Set(["factset", "intex", "maplecroft", "yfinance"]);

interface VendorCardProps {
  vendorKey: string;
  name: string;
  description: string;
  category: string;
  datasetCount: number;
  website?: string;
}

export default function VendorCard({
  vendorKey,
  name,
  description,
  category,
  datasetCount,
  website,
}: VendorCardProps) {
  const ext = SVG_VENDORS.has(vendorKey) ? "svg" : "png";
  const [imgError, setImgError] = useState(false);

  return (
    <Box
      sx={{
        display: "flex",
        gap: 2.5,
        py: 2,
        borderBottom: "1px solid rgba(0,0,0,0.08)",
        "&:last-child": { borderBottom: "none" },
        position: "relative",
      }}
    >
      {/* Vendor logo — links to external website if available */}
      <Box
        component={website ? "a" : "div"}
        {...(website ? { href: website, target: "_blank", rel: "noopener noreferrer" } : {})}
        sx={{
          width: 56,
          height: 56,
          borderRadius: "8px",
          border: "1px solid rgba(0,0,0,0.08)",
          bgcolor: "white",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
          overflow: "hidden",
          mt: 0.3,
          cursor: website ? "pointer" : "default",
          textDecoration: "none",
          transition: "box-shadow 0.15s",
          "&:hover": website ? { boxShadow: "0 0 0 2px rgba(0,85,135,0.3)" } : {},
        }}
      >
        {imgError ? (
          <Typography sx={{ fontWeight: 700, fontSize: "1rem", color: "#022D5E" }}>
            {name.slice(0, 2).toUpperCase()}
          </Typography>
        ) : (
          <Image
            src={`/assets/${vendorKey}.${ext}`}
            alt={`${name} logo`}
            width={40}
            height={40}
            style={{ objectFit: "contain" }}
            onError={() => setImgError(true)}
          />
        )}
      </Box>

      {/* Name, description, category */}
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
            <Link
              href={`/datasets?vendor=${vendorKey}`}
              style={{ color: "inherit", textDecoration: "none" }}
              onMouseOver={(e) =>
                (e.currentTarget.style.textDecoration = "underline")
              }
              onMouseOut={(e) =>
                (e.currentTarget.style.textDecoration = "none")
              }
            >
              {name}
            </Link>
          </Typography>
          <Box sx={{ flexGrow: 1 }} />
          {/* Dataset count pill badge — right-aligned */}
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
        </Box>
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
