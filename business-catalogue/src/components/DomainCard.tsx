"use client";
import { Box, Typography } from "@mui/material";
import Link from "next/link";

interface DomainCardProps {
  domainKey: string;
  displayName: string;
  color: string;
  datasetCount: number;
}

export default function DomainCard({
  domainKey,
  displayName,
  color,
  datasetCount,
}: DomainCardProps) {
  return (
    <Link href={`/domains/${domainKey}`} style={{ textDecoration: "none" }}>
      <Box
        sx={{
          position: "relative",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          borderRadius: "4px",
          p: 2.5,
          minHeight: 120,
          textAlign: "center",
          cursor: "pointer",
          transition: "background-color 0.15s",
          "&:hover": {
            bgcolor: "rgba(0,0,0,0.04)",
          },
        }}
      >
        {/* Count badge */}
        <Typography
          component="span"
          sx={{
            position: "absolute",
            top: 8,
            right: 8,
            color: "#8c8f93",
            fontSize: "0.7rem",
            fontWeight: 400,
          }}
        >
          {datasetCount}
        </Typography>

        {/* Color dot */}
        <Box
          sx={{
            width: 32,
            height: 32,
            borderRadius: "50%",
            bgcolor: color,
            mb: 1.5,
            flexShrink: 0,
          }}
        />

        <Typography
          variant="body2"
          sx={{
            color: "#000",
            fontWeight: 600,
            lineHeight: 1.3,
          }}
        >
          {displayName}
        </Typography>
      </Box>
    </Link>
  );
}
