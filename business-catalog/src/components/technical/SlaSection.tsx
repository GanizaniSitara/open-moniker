"use client";
import { Typography, Box, Paper, Chip } from "@mui/material";
import { TechnicalProfile } from "@/lib/tech-catalog-types";

interface Props {
  sla: TechnicalProfile["sla"];
}

const healthColor: Record<string, "success" | "warning" | "error"> = {
  healthy: "success",
  degraded: "warning",
  critical: "error",
};

export default function SlaSection({ sla }: Props) {
  return (
    <Box sx={{ mb: 4 }}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}>
        <Typography variant="h5" sx={{ color: "#022D5E" }}>
          SLA &amp; Health
        </Typography>
        <Chip
          label={sla.health_status}
          size="small"
          color={healthColor[sla.health_status]}
        />
      </Box>
      <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
        {[
          ["Availability Target", sla.availability_target],
          ["Current Availability", sla.current_availability],
          ["RTO", `${sla.rto_hours} hour${sla.rto_hours !== 1 ? "s" : ""}`],
          ["RPO", `${sla.rpo_hours} hour${sla.rpo_hours !== 1 ? "s" : ""}`],
          ["P1 Response", `${sla.p1_response_minutes} min`],
          ["Last Incident", sla.last_incident],
        ].map(([label, value]) => (
          <Paper key={label} variant="outlined" sx={{ p: 2, flex: 1, minWidth: 150 }}>
            <Typography variant="caption" color="text.secondary">
              {label}
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {value}
            </Typography>
          </Paper>
        ))}
      </Box>
    </Box>
  );
}
