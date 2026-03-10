"use client";
import { useState, useMemo } from "react";
import { Box, TextField, InputAdornment, Typography } from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
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
    owner: string;
  }[];
}

export default function DomainGrid({ domains }: DomainGridProps) {
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    if (!search) return domains;
    const q = search.toLowerCase();
    return domains.filter(
      (d) =>
        d.displayName.toLowerCase().includes(q) ||
        d.notes.toLowerCase().includes(q) ||
        d.owner.toLowerCase().includes(q)
    );
  }, [domains, search]);

  return (
    <Box sx={{ ml: "252px" }}>
      <TextField
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search domains..."
        fullWidth
        variant="outlined"
        size="small"
        sx={{ mb: 1 }}
        slotProps={{
          input: {
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon sx={{ color: "#53565A" }} />
              </InputAdornment>
            ),
          },
        }}
      />
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {filtered.length} domains
      </Typography>
      {filtered.map((d) => (
        <DomainCard
          key={d.domainKey}
          domainKey={d.domainKey}
          displayName={d.displayName}
          color={d.color}
          notes={d.notes}
          dataCategory={d.dataCategory}
          confidentiality={d.confidentiality}
          owner={d.owner}
          datasetCount={d.datasetCount}
        />
      ))}
    </Box>
  );
}
