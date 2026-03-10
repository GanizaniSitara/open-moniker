"use client";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Chip,
} from "@mui/material";
import Link from "next/link";
import type { Dataset } from "@/lib/types";

interface AppearsInEntry {
  dataset: Dataset;
  columnName?: string;
  notes?: string;
}

export default function AppearsInTable({
  entries,
}: {
  entries: AppearsInEntry[];
}) {
  if (entries.length === 0) return null;

  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow sx={{ bgcolor: "#f8f9fa" }}>
            <TableCell sx={{ fontWeight: 600 }}>Dataset</TableCell>
            <TableCell sx={{ fontWeight: 600 }}>Column Name</TableCell>
            <TableCell sx={{ fontWeight: 600 }}>Source Type</TableCell>
            <TableCell sx={{ fontWeight: 600 }}>Notes</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {entries.map((e) => (
            <TableRow key={e.dataset.key}>
              <TableCell>
                <Link
                  href={`/datasets/${e.dataset.key}`}
                  style={{ textDecoration: "none" }}
                >
                  <Typography
                    variant="body2"
                    sx={{
                      color: "#005587",
                      fontWeight: 500,
                      "&:hover": { textDecoration: "underline" },
                    }}
                  >
                    {e.dataset.display_name}
                  </Typography>
                </Link>
                <Typography variant="caption" display="block" color="text.secondary">
                  {e.dataset.key}
                </Typography>
              </TableCell>
              <TableCell>
                {e.columnName && (
                  <Chip
                    label={e.columnName}
                    size="small"
                    sx={{ fontFamily: "monospace" }}
                  />
                )}
              </TableCell>
              <TableCell>
                {e.dataset.source_binding && (
                  <Chip
                    label={e.dataset.source_binding.type.toUpperCase()}
                    size="small"
                    variant="outlined"
                  />
                )}
              </TableCell>
              <TableCell>
                <Typography variant="body2" color="text.secondary">
                  {e.notes}
                </Typography>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
