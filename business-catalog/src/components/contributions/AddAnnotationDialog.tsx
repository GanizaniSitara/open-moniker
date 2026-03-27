"use client";
import { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import AuthorInput, { useAuthor } from "./AuthorInput";
import { createAnnotation } from "@/lib/contributions-client";
import type { AnnotationType } from "@/lib/contributions-types";

const ANNOTATION_TYPES: { value: AnnotationType; label: string }[] = [
  { value: "tip", label: "Tip" },
  { value: "warning", label: "Warning" },
  { value: "context", label: "Context" },
  { value: "usage", label: "Usage" },
];

interface AddAnnotationDialogProps {
  open: boolean;
  onClose: () => void;
  entityType: string;
  entityKey: string;
  onCreated?: () => void;
}

export default function AddAnnotationDialog({
  open,
  onClose,
  entityType,
  entityKey,
  onCreated,
}: AddAnnotationDialogProps) {
  const [author, setAuthor] = useAuthor();
  const [showAuthor, setShowAuthor] = useState(false);
  const [type, setType] = useState<AnnotationType>("tip");
  const [content, setContent] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (authorName?: string) => {
    const name = authorName || author;
    if (!name) {
      setShowAuthor(true);
      return;
    }
    if (!content.trim()) return;

    setSubmitting(true);
    try {
      await createAnnotation({
        entityType,
        entityKey,
        annotationType: type,
        content: content.trim(),
        author: name,
      });
      setContent("");
      setType("tip");
      onClose();
      onCreated?.();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ color: "#022D5E", fontSize: "1rem" }}>
          Add Annotation
        </DialogTitle>
        <DialogContent>
          <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: "block" }}>
            Type
          </Typography>
          <ToggleButtonGroup
            value={type}
            exclusive
            onChange={(_, v) => v && setType(v)}
            size="small"
            sx={{ mb: 2 }}
          >
            {ANNOTATION_TYPES.map((t) => (
              <ToggleButton key={t.value} value={t.value} sx={{ textTransform: "none", fontSize: "0.8rem" }}>
                {t.label}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
          <TextField
            fullWidth
            multiline
            rows={4}
            size="small"
            label="Content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} size="small">
            Cancel
          </Button>
          <Button
            onClick={() => handleSubmit()}
            disabled={submitting || !content.trim()}
            variant="contained"
            size="small"
            sx={{ bgcolor: "#789D4A" }}
          >
            Add
          </Button>
        </DialogActions>
      </Dialog>

      <AuthorInput
        open={showAuthor}
        onClose={() => setShowAuthor(false)}
        onSubmit={(name) => {
          setAuthor(name);
          setShowAuthor(false);
          handleSubmit(name);
        }}
      />
    </>
  );
}
