"use client";
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  Container,
} from "@mui/material";
import StorageIcon from "@mui/icons-material/Storage";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_LINKS = [
  { label: "Datasets", href: "/" },
  { label: "Domains", href: "/domains" },
  { label: "Fields", href: "/fields" },
];

export default function AppHeader() {
  const pathname = usePathname();

  return (
    <AppBar position="sticky" elevation={0} sx={{ bgcolor: "#022D5E" }}>
      <Container maxWidth="xl">
        <Toolbar disableGutters sx={{ minHeight: 48 }}>
          <StorageIcon sx={{ mr: 1.5, fontSize: 20 }} />
          <Link href="/" style={{ textDecoration: "none", color: "inherit", marginRight: 32 }}>
            <Typography
              variant="body1"
              sx={{ fontWeight: 700, color: "white" }}
            >
              Business Catalogue
            </Typography>
          </Link>
          <Box sx={{ display: "flex", gap: 0.5 }}>
            {NAV_LINKS.map((link) => {
              const active =
                link.href === "/"
                  ? pathname === "/" || pathname === "/datasets"
                  : pathname.startsWith(link.href);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  style={{ textDecoration: "none" }}
                >
                  <Typography
                    variant="body2"
                    sx={{
                      color: "white",
                      px: 1.5,
                      py: 0.5,
                      borderRadius: "4px",
                      bgcolor: active ? "#005587" : "transparent",
                      "&:hover": {
                        bgcolor: active ? "#005587" : "rgba(255,255,255,0.1)",
                      },
                    }}
                  >
                    {link.label}
                  </Typography>
                </Link>
              );
            })}
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}
