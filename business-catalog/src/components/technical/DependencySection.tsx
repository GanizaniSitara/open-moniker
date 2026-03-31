"use client";
import { Typography, Box, Paper, Chip } from "@mui/material";
import Link from "next/link";
import { Dependency } from "@/lib/tech-catalog-types";

interface Props {
  upstream: Dependency[];
  downstream: Dependency[];
}

const critColor: Record<string, "error" | "warning" | "info" | "default"> = {
  critical: "error",
  high: "warning",
  medium: "info",
  low: "default",
};

function DepCard({ dep }: { dep: Dependency }) {
  return (
    <Link
      href={`/technical/${dep.app_key}`}
      style={{ textDecoration: "none", color: "inherit" }}
    >
      <Paper
        variant="outlined"
        sx={{
          p: 1.5,
          mb: 1,
          "&:hover": { borderColor: "#005587" },
          cursor: "pointer",
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
          <Typography
            variant="body2"
            sx={{ fontWeight: 600, color: "#005587" }}
          >
            {dep.display_name}
          </Typography>
          <Chip
            label={dep.criticality}
            size="small"
            color={critColor[dep.criticality]}
            sx={{ fontSize: "0.7rem", height: 20 }}
          />
        </Box>
        <Typography variant="caption" sx={{ color: "#53565A" }}>
          {dep.type} · {dep.protocol}
          {dep.notes ? ` · ${dep.notes}` : ""}
        </Typography>
      </Paper>
    </Link>
  );
}

export default function DependencySection({ upstream, downstream }: Props) {
  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h5" sx={{ mb: 1.5, color: "#022D5E" }}>
        Dependencies
      </Typography>
      <Box sx={{ display: "flex", gap: 3, flexWrap: { xs: "wrap", md: "nowrap" } }}>
        <Box sx={{ flex: 1, minWidth: 250 }}>
          <Typography variant="h6" sx={{ mb: 1, fontSize: "0.95rem", color: "#022D5E" }}>
            Upstream ({upstream.length})
          </Typography>
          {upstream.length > 0 ? (
            upstream.map((d) => <DepCard key={d.app_key} dep={d} />)
          ) : (
            <Typography variant="body2" color="text.secondary">
              No upstream dependencies.
            </Typography>
          )}
        </Box>
        <Box sx={{ flex: 1, minWidth: 250 }}>
          <Typography variant="h6" sx={{ mb: 1, fontSize: "0.95rem", color: "#022D5E" }}>
            Downstream ({downstream.length})
          </Typography>
          {downstream.length > 0 ? (
            downstream.map((d) => <DepCard key={d.app_key} dep={d} />)
          ) : (
            <Typography variant="body2" color="text.secondary">
              No downstream dependencies.
            </Typography>
          )}
        </Box>
      </Box>
    </Box>
  );
}
