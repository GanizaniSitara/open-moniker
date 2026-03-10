"use client";
import { Box } from "@mui/material";
import CategoryCard from "./CategoryCard";

interface CategoryGridProps {
  categories: {
    domainKey: string;
    displayName: string;
    notes: string;
    color: string;
    dataCategory: string;
    datasetCount: number;
    confidentiality: string;
  }[];
}

export default function CategoryGrid({ categories }: CategoryGridProps) {
  return (
    <Box
      sx={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
        gap: "1rem",
      }}
    >
      {categories.map((cat) => (
        <CategoryCard
          key={cat.domainKey}
          domainKey={cat.domainKey}
          displayName={cat.displayName}
          color={cat.color}
          datasetCount={cat.datasetCount}
        />
      ))}
    </Box>
  );
}
