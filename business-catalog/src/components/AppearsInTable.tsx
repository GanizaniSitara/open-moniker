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

interface AppearsInEntry {
  datasetKey: string;
  displayName: string;
  sourceType?: string;
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
    <TableContainer component={Paper} variant="outlined" sx={{ overflowX: "auto" }}>
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
            <TableRow key={e.datasetKey}>
              <TableCell>
                <Link
                  href={`/datasets/${e.datasetKey}`}
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
                    {e.displayName}
                  </Typography>
                </Link>
                <Typography variant="caption" display="block" color="text.secondary">
                  {e.datasetKey}
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
                {e.sourceType && (
                  <Chip
                    label={e.sourceType.toUpperCase()}
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
