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
  Chip,
} from "@mui/material";
import { ApiEndpoint } from "@/lib/tech-catalogue-types";

interface Props {
  endpoints: ApiEndpoint[];
}

const methodColor: Record<string, string> = {
  GET: "#009639",
  POST: "#005587",
  PUT: "#F39C12",
  DELETE: "#D0002B",
  PATCH: "#8E44AD",
};

export default function ApiEndpointTable({ endpoints }: Props) {
  if (endpoints.length === 0) return null;

  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h5" sx={{ mb: 1.5, color: "#022D5E" }}>
        API Endpoints
      </Typography>
      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 600 }}>Method</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Path</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Description</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Auth</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Rate Limit</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {endpoints.map((ep, i) => (
              <TableRow key={i}>
                <TableCell>
                  <Chip
                    label={ep.method}
                    size="small"
                    sx={{
                      bgcolor: methodColor[ep.method] || "#53565A",
                      color: "white",
                      fontWeight: 700,
                      fontSize: "0.7rem",
                      height: 22,
                    }}
                  />
                </TableCell>
                <TableCell sx={{ fontFamily: "monospace", fontSize: "0.8rem" }}>
                  {ep.path}
                </TableCell>
                <TableCell>{ep.description}</TableCell>
                <TableCell sx={{ fontSize: "0.85rem" }}>{ep.auth}</TableCell>
                <TableCell sx={{ fontSize: "0.85rem" }}>{ep.rate_limit || "—"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
