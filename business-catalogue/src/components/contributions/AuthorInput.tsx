"use client";
import { useState, useEffect } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Typography,
} from "@mui/material";

const STORAGE_KEY = "contributions_author";

export function useAuthor(): [string, (name: string) => void] {
  const [author, setAuthor] = useState("");

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) setAuthor(stored);
  }, []);

  const save = (name: string) => {
    setAuthor(name);
    localStorage.setItem(STORAGE_KEY, name);
  };

  return [author, save];
}

interface AuthorInputProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (name: string) => void;
}

export default function AuthorInput({ open, onClose, onSubmit }: AuthorInputProps) {
  const [name, setName] = useState("");

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle sx={{ color: "#022D5E" }}>Who are you?</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Your name will appear on contributions you make.
        </Typography>
        <TextField
          autoFocus
          fullWidth
          size="small"
          label="Your name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && name.trim()) {
              onSubmit(name.trim());
            }
          }}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} size="small">
          Cancel
        </Button>
        <Button
          onClick={() => onSubmit(name.trim())}
          disabled={!name.trim()}
          variant="contained"
          size="small"
          sx={{ bgcolor: "#005587" }}
        >
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
}
