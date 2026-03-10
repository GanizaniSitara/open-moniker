"use client";
import { Box } from "@mui/material";
import DomainCard from "./DomainCard";

interface DomainGridProps {
  domains: {
    domainKey: string;
    displayName: string;
    notes: string;
    color: string;
    dataCategory: string;
    datasetCount: number;
    confidentiality: string;
  }[];
}

export default function DomainGrid({ domains }: DomainGridProps) {
  return (
    <Box
      sx={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
        gap: "1rem",
      }}
    >
      {domains.map((d) => (
        <DomainCard
          key={d.domainKey}
          domainKey={d.domainKey}
          displayName={d.displayName}
          color={d.color}
          datasetCount={d.datasetCount}
        />
      ))}
    </Box>
  );
}
