"use client";
import {
  Breadcrumbs as MuiBreadcrumbs,
  Typography,
  Box,
} from "@mui/material";
import Link from "next/link";
import NavigateNextIcon from "@mui/icons-material/NavigateNext";

interface BreadcrumbItem {
  label: string;
  href?: string;
}

export default function Breadcrumbs({ items }: { items: BreadcrumbItem[] }) {
  return (
    <Box
      data-testid="breadcrumbs-bar"
      sx={{
        bgcolor: "#e9ecef",
        px: 3,
        py: 1,
      }}
    >
      <MuiBreadcrumbs
        separator={<NavigateNextIcon sx={{ fontSize: 16 }} />}
        sx={{ "& .MuiBreadcrumbs-ol": { flexWrap: "nowrap" } }}
      >
        <Link href="/" style={{ color: "inherit", textDecoration: "none" }}>
          <Typography variant="body2" sx={{ "&:hover": { textDecoration: "underline" } }}>
            Home
          </Typography>
        </Link>
        {items.map((item, i) =>
          item.href && i < items.length - 1 ? (
            <Link
              key={i}
              href={item.href}
              style={{ color: "inherit", textDecoration: "none" }}
            >
              <Typography variant="body2" sx={{ "&:hover": { textDecoration: "underline" } }}>
                {item.label}
              </Typography>
            </Link>
          ) : (
            <Typography key={i} variant="body2" color="text.primary">
              {item.label}
            </Typography>
          )
        )}
      </MuiBreadcrumbs>
    </Box>
  );
}
