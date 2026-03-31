"use client";
import { Box, Typography, Container } from "@mui/material";
import Link from "next/link";

export default function HeroSection() {
  return (
    <Box
      sx={{
        bgcolor: "#f0f2f5",
        py: 5,
      }}
    >
      <Container maxWidth="lg">
        <Box sx={{ maxWidth: 640 }}>
          <Typography
            variant="h3"
            sx={{ fontWeight: 700, mb: 1.5, color: "#022D5E" }}
          >
            Data Catalog
          </Typography>
          <Typography
            variant="body1"
            sx={{ mb: 2.5, color: "#53565A", lineHeight: 1.6 }}
          >
            Discover and explore the firm&apos;s data assets across domains,
            datasets, and business fields.
          </Typography>
          <Link
            href="/datasets"
            style={{
              color: "#005587",
              fontWeight: 600,
              textDecoration: "none",
            }}
          >
            Browse all datasets &rarr;
          </Link>
        </Box>
      </Container>
    </Box>
  );
}
