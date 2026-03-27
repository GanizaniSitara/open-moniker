"use client";
import { Typography, Box, Paper } from "@mui/material";
import { TechnicalProfile } from "@/lib/tech-catalog-types";

interface Props {
  cmdb: TechnicalProfile["cmdb"];
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <Paper variant="outlined" sx={{ p: 2, flex: 1, minWidth: 180 }}>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="body2" sx={{ fontFamily: "monospace" }}>
        {value}
      </Typography>
    </Paper>
  );
}

export default function CmdbSection({ cmdb }: Props) {
  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h5" sx={{ mb: 1.5, color: "#022D5E" }}>
        CMDB Metadata
      </Typography>
      <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
        <Field label="CI ID" value={cmdb.ci_id} />
        <Field label="CI Class" value={cmdb.ci_class} />
        <Field label="Operational Status" value={cmdb.operational_status} />
        <Field label="Business Criticality" value={cmdb.business_criticality} />
      </Box>
      <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", mt: 2 }}>
        <Field label="Change Group" value={cmdb.change_group} />
        <Field label="Assignment Group" value={cmdb.assignment_group} />
        <Field label="Cost Center" value={cmdb.cost_center} />
        <Field label="Attestation Date" value={cmdb.attestation_date} />
      </Box>
    </Box>
  );
}
