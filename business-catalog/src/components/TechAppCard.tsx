"use client";
import { Typography, Box, Chip, LinearProgress } from "@mui/material";
import Link from "next/link";
import { TechnicalProfile } from "@/lib/tech-catalog-types";

interface TechAppCardProps {
  appKey: string;
  displayName: string;
  color: string;
  profile: TechnicalProfile;
}

const healthColor: Record<string, "success" | "warning" | "error"> = {
  healthy: "success",
  degraded: "warning",
  critical: "error",
};

const criticalityLabel: Record<string, string> = {
  "1-critical": "Critical",
  "2-high": "High",
  "3-medium": "Medium",
  "4-low": "Low",
};

export default function TechAppCard({
  appKey,
  displayName,
  color,
  profile,
}: TechAppCardProps) {
  const depCount =
    profile.dependencies.upstream.length +
    profile.dependencies.downstream.length;

  return (
    <Link
      href={`/technical/${appKey}`}
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
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
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
              {/* Health dot */}
              <Box
                sx={{
                  width: 10,
                  height: 10,
                  borderRadius: "50%",
                  bgcolor:
                    profile.sla.health_status === "healthy"
                      ? "#009639"
                      : profile.sla.health_status === "degraded"
                      ? "#FFD100"
                      : "#D0002B",
                  flexShrink: 0,
                }}
              />
            </Box>
            <Box sx={{ flexGrow: 1 }} />
            <Box sx={{ display: "flex", gap: 0.5, flexShrink: 0 }}>
              <Chip
                label={profile.cmdb.ci_id}
                size="small"
                sx={{
                  bgcolor: "#022D5E",
                  color: "white",
                  fontWeight: 600,
                  fontSize: "0.7rem",
                  height: 22,
                  fontFamily: "monospace",
                }}
              />
              {depCount > 0 && (
                <Chip
                  label={`${depCount} deps`}
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

          {/* Infrastructure summary */}
          <Typography
            variant="body2"
            sx={{ color: "#53565A", lineHeight: 1.5 }}
          >
            {profile.infrastructure.hosting} · {profile.infrastructure.region} ·{" "}
            {profile.infrastructure.environments.length} env
            {profile.infrastructure.environments.length !== 1 ? "s" : ""}
          </Typography>

          {/* Tech debt bar */}
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 0.5, mb: 0.5 }}>
            <Typography variant="caption" sx={{ color: "#53565A", minWidth: 60 }}>
              Tech debt
            </Typography>
            <LinearProgress
              variant="determinate"
              value={profile.tech_debt.score}
              sx={{
                flexGrow: 1,
                height: 6,
                borderRadius: 3,
                bgcolor: "#e9ecef",
                "& .MuiLinearProgress-bar": {
                  bgcolor:
                    profile.tech_debt.score > 60
                      ? "#D0002B"
                      : profile.tech_debt.score > 35
                      ? "#FFD100"
                      : "#009639",
                  borderRadius: 3,
                },
              }}
            />
            <Typography variant="caption" sx={{ color: "#53565A", minWidth: 24, textAlign: "right" }}>
              {profile.tech_debt.score}
            </Typography>
          </Box>

          <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
            <Chip
              label={profile.infrastructure.hosting}
              size="small"
              variant="outlined"
              sx={{ fontSize: "0.7rem" }}
            />
            <Chip
              label={criticalityLabel[profile.cmdb.business_criticality]}
              size="small"
              variant="outlined"
              sx={{ fontSize: "0.7rem" }}
            />
            <Chip
              label={profile.sla.health_status}
              size="small"
              color={healthColor[profile.sla.health_status]}
              sx={{ fontSize: "0.7rem" }}
            />
          </Box>
        </Box>
      </Box>
    </Link>
  );
}
