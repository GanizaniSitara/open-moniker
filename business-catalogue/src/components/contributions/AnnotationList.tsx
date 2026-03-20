"use client";
import { useEffect, useState, useCallback } from "react";
import { Box, Button, Typography } from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import AnnotationCard from "./AnnotationCard";
import AddAnnotationDialog from "./AddAnnotationDialog";
import { fetchAnnotations } from "@/lib/contributions-client";
import type { Annotation } from "@/lib/contributions-types";

interface AnnotationListProps {
  entityType: string;
  entityKey: string;
}

export default function AnnotationList({ entityType, entityKey }: AnnotationListProps) {
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [showAdd, setShowAdd] = useState(false);

  const load = useCallback(() => {
    fetchAnnotations(entityType, entityKey).then(setAnnotations).catch(() => {});
  }, [entityType, entityKey]);

  useEffect(() => { load(); }, [load]);

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", mb: 1.5 }}>
        <Typography variant="subtitle2" sx={{ flexGrow: 1, color: "#022D5E" }}>
          Annotations ({annotations.length})
        </Typography>
        <Button
          size="small"
          startIcon={<AddIcon />}
          onClick={() => setShowAdd(true)}
          sx={{ textTransform: "none", fontSize: "0.8rem", color: "#789D4A" }}
        >
          Add
        </Button>
      </Box>

      {annotations.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          No annotations yet. Share your knowledge!
        </Typography>
      ) : (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
          {annotations.map((a) => (
            <AnnotationCard key={a.id} annotation={a} onVoteChange={load} />
          ))}
        </Box>
      )}

      <AddAnnotationDialog
        open={showAdd}
        onClose={() => setShowAdd(false)}
        entityType={entityType}
        entityKey={entityKey}
        onCreated={load}
      />
    </Box>
  );
}
