"use client";
import { useState } from "react";
import {
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from "@mui/material";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import AuthorInput, { useAuthor } from "./AuthorInput";
import { isContributionsEnabled, createSuggestion } from "@/lib/contributions-client";

export interface SuggestEditField {
  name: string;
  label: string;
  currentValue?: string | null;
}

interface SuggestEditButtonProps {
  entityType: string;
  entityKey: string;
  fields: SuggestEditField[];
}

export default function SuggestEditButton({ entityType, entityKey, fields }: SuggestEditButtonProps) {
  const [author, setAuthor] = useAuthor();
  const [open, setOpen] = useState(false);
  const [selectedField, setSelectedField] = useState("");
  const [proposedValue, setProposedValue] = useState("");
  const [reason, setReason] = useState("");
  const [showAuthor, setShowAuthor] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  if (!isContributionsEnabled()) return null;

  const currentField = fields.find((f) => f.name === selectedField);

  const reset = () => {
    setSelectedField("");
    setProposedValue("");
    setReason("");
    setSubmitted(false);
  };

  const handleOpen = () => {
    reset();
    setOpen(true);
  };

  const handleSubmit = async (authorName?: string) => {
    const name = authorName || author;
    if (!name) {
      setShowAuthor(true);
      return;
    }
    if (!selectedField || !proposedValue.trim()) return;

    setSubmitting(true);
    try {
      await createSuggestion({
        entityType,
        entityKey,
        fieldName: selectedField,
        currentValue: currentField?.currentValue || undefined,
        proposedValue: proposedValue.trim(),
        reason: reason.trim() || undefined,
        author: name,
      });
      setSubmitted(true);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <Box
        component="button"
        onClick={handleOpen}
        sx={{
          display: "inline-flex",
          alignItems: "center",
          gap: 0.5,
          background: "none",
          border: "none",
          cursor: "pointer",
          color: "#005587",
          fontSize: "0.85rem",
          p: 0,
          mt: 1,
          "&:hover": { textDecoration: "underline" },
        }}
      >
        <EditOutlinedIcon sx={{ fontSize: 16 }} />
        Suggest an edit
      </Box>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ color: "#022D5E", fontSize: "1rem" }}>
          Suggest an Edit
        </DialogTitle>
        <DialogContent>
          {submitted ? (
            <Typography variant="body1" sx={{ py: 2, color: "#009639" }}>
              Thank you! Your suggestion has been submitted.
            </Typography>
          ) : (
            <Box sx={{ display: "flex", flexDirection: "column", gap: 2, mt: 1 }}>
              <FormControl size="small" fullWidth>
                <InputLabel>Field</InputLabel>
                <Select
                  value={selectedField}
                  label="Field"
                  onChange={(e) => {
                    setSelectedField(e.target.value);
                    setProposedValue("");
                  }}
                >
                  {fields.map((f) => (
                    <MenuItem key={f.name} value={f.name}>
                      {f.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {currentField && (
                <TextField
                  size="small"
                  label="Current value"
                  value={currentField.currentValue || "(empty)"}
                  fullWidth
                  InputProps={{ readOnly: true }}
                  sx={{ "& .MuiInputBase-input": { color: "#6B7280" } }}
                />
              )}

              <TextField
                size="small"
                label="Proposed value"
                value={proposedValue}
                onChange={(e) => setProposedValue(e.target.value)}
                fullWidth
                multiline
                rows={2}
              />

              <TextField
                size="small"
                label="Reason (optional)"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                fullWidth
                multiline
                rows={2}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)} size="small">
            {submitted ? "Close" : "Cancel"}
          </Button>
          {!submitted && (
            <Button
              onClick={() => handleSubmit()}
              disabled={submitting || !selectedField || !proposedValue.trim()}
              variant="contained"
              size="small"
              sx={{ bgcolor: "#005587" }}
            >
              Submit Suggestion
            </Button>
          )}
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
