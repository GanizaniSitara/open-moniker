"use client";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Typography,
} from "@mui/material";
import KeyIcon from "@mui/icons-material/Key";

interface Column {
  name: string;
  type: string;
  description?: string;
  semantic_type?: string;
  primary_key?: boolean;
  foreign_key?: string;
}

export default function SchemaTable({ columns }: { columns: Column[] }) {
  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow sx={{ bgcolor: "grey.50" }}>
            <TableCell sx={{ fontWeight: 600 }}>Column</TableCell>
            <TableCell sx={{ fontWeight: 600 }}>Type</TableCell>
            <TableCell sx={{ fontWeight: 600 }}>Description</TableCell>
            <TableCell sx={{ fontWeight: 600 }}>Semantic Type</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {columns.map((col) => (
            <TableRow key={col.name}>
              <TableCell>
                <Typography
                  variant="body2"
                  sx={{ fontFamily: "monospace", fontWeight: 500 }}
                >
                  {col.primary_key && (
                    <KeyIcon
                      sx={{
                        fontSize: 14,
                        mr: 0.5,
                        color: "warning.main",
                        verticalAlign: "middle",
                      }}
                    />
                  )}
                  {col.name}
                </Typography>
              </TableCell>
              <TableCell>
                <Chip
                  label={col.type}
                  size="small"
                  variant="outlined"
                  sx={{ fontFamily: "monospace", fontSize: "0.75rem" }}
                />
              </TableCell>
              <TableCell>
                <Typography variant="body2">{col.description}</Typography>
              </TableCell>
              <TableCell>
                {col.semantic_type && (
                  <Chip label={col.semantic_type} size="small" color="info" />
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
