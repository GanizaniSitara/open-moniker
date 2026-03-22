"use client";
import {
  Typography,
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@mui/material";
import { TechnicalProfile } from "@/lib/tech-catalogue-types";

interface Props {
  infrastructure: TechnicalProfile["infrastructure"];
}

export default function InfraSection({ infrastructure }: Props) {
  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h5" sx={{ mb: 1.5, color: "#022D5E" }}>
        Infrastructure
      </Typography>
      <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", mb: 2 }}>
        {[
          ["Hosting", infrastructure.hosting],
          ["Region", infrastructure.region],
          ["Compute", infrastructure.compute],
          ["Storage", infrastructure.storage],
          ["Network Zone", infrastructure.network_zone],
          ["Disaster Recovery", infrastructure.disaster_recovery],
          ["Backup Frequency", infrastructure.backup_frequency],
        ].map(([label, value]) => (
          <Paper key={label} variant="outlined" sx={{ p: 2, flex: 1, minWidth: 200 }}>
            <Typography variant="caption" color="text.secondary">
              {label}
            </Typography>
            <Typography variant="body2">{value}</Typography>
          </Paper>
        ))}
      </Box>

      <Typography variant="h6" sx={{ mb: 1, color: "#022D5E", fontSize: "1rem" }}>
        Environments
      </Typography>
      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 600 }}>Name</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>URL</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Version</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Last Deployed</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {infrastructure.environments.map((env) => (
              <TableRow key={env.name}>
                <TableCell>{env.name}</TableCell>
                <TableCell sx={{ fontFamily: "monospace", fontSize: "0.8rem" }}>
                  {env.url}
                </TableCell>
                <TableCell sx={{ fontFamily: "monospace", fontSize: "0.8rem" }}>
                  {env.version}
                </TableCell>
                <TableCell>{env.last_deployed}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
