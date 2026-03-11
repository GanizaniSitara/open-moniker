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
} from "@mui/material";
import Link from "next/link";
interface RelatedModel {
  path?: string;
  key?: string;
  display_name: string;
  description?: string;
  formula?: string | null;
  unit?: string | null;
}

interface RelatedModelsProps {
  models: RelatedModel[];
}

export default function RelatedModels({ models }: RelatedModelsProps) {
  if (models.length === 0) return null;

  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow sx={{ bgcolor: "#f8f9fa" }}>
            <TableCell sx={{ fontWeight: 600 }}>Model</TableCell>
            <TableCell sx={{ fontWeight: 600 }}>Description</TableCell>
            <TableCell sx={{ fontWeight: 600 }}>Formula</TableCell>
            <TableCell sx={{ fontWeight: 600 }}>Unit</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {models.map((m) => (
            <TableRow key={m.path || m.key}>
              <TableCell>
                <Link
                  href={`/fields/${m.path || m.key}`}
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
                    {m.display_name}
                  </Typography>
                </Link>
              </TableCell>
              <TableCell>
                <Typography variant="body2">{m.description}</Typography>
              </TableCell>
              <TableCell>
                <Typography
                  variant="body2"
                  sx={{ fontFamily: "monospace", fontSize: "0.8rem" }}
                >
                  {m.formula}
                </Typography>
              </TableCell>
              <TableCell>
                <Typography variant="body2">{m.unit}</Typography>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
