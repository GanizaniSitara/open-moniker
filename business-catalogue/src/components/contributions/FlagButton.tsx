"use client";
import { useState } from "react";
import {
  Button,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  TextField,
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from "@mui/material";
import FlagIcon from "@mui/icons-material/Flag";
import ErrorIcon from "@mui/icons-material/Error";
import HelpIcon from "@mui/icons-material/Help";
import UpdateIcon from "@mui/icons-material/Update";
import WarningIcon from "@mui/icons-material/Warning";
import AuthorInput, { useAuthor } from "./AuthorInput";
import { createFlag } from "@/lib/contributions-client";
import type { FlagType } from "@/lib/contributions-types";

const FLAG_TYPES: { value: FlagType; label: string; icon: React.ReactNode }[] = [
  { value: "outdated", label: "Outdated", icon: <UpdateIcon fontSize="small" /> },
  { value: "incorrect", label: "Incorrect", icon: <ErrorIcon fontSize="small" /> },
  { value: "missing", label: "Missing Info", icon: <WarningIcon fontSize="small" /> },
  { value: "unclear", label: "Unclear", icon: <HelpIcon fontSize="small" /> },
];

interface FlagButtonProps {
  entityType: string;
  entityKey: string;
  onFlagged?: () => void;
}

export default function FlagButton({ entityType, entityKey, onFlagged }: FlagButtonProps) {
  const [author, setAuthor] = useAuthor();
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const [selectedType, setSelectedType] = useState<FlagType | null>(null);
  const [comment, setComment] = useState("");
  const [showAuthor, setShowAuthor] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleTypeSelect = (type: FlagType) => {
    setAnchorEl(null);
    setSelectedType(type);
    setComment("");
  };

  const handleSubmit = async (authorName?: string) => {
    const name = authorName || author;
    if (!name) {
      setShowAuthor(true);
      return;
    }
    if (!selectedType) return;

    setSubmitting(true);
    try {
      await createFlag({
        entityType,
        entityKey,
        flagType: selectedType,
        comment: comment || undefined,
        author: name,
      });
      setSelectedType(null);
      setComment("");
      onFlagged?.();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <Button
        size="small"
        startIcon={<FlagIcon />}
        onClick={(e) => setAnchorEl(e.currentTarget)}
        sx={{ color: "#53565A", textTransform: "none", fontSize: "0.8rem" }}
      >
        Flag
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={() => setAnchorEl(null)}
      >
        {FLAG_TYPES.map((ft) => (
          <MenuItem key={ft.value} onClick={() => handleTypeSelect(ft.value)}>
            <ListItemIcon sx={{ minWidth: 32 }}>{ft.icon}</ListItemIcon>
            <ListItemText primaryTypographyProps={{ variant: "body2" }}>
              {ft.label}
            </ListItemText>
          </MenuItem>
        ))}
      </Menu>

      <Dialog
        open={selectedType !== null}
        onClose={() => setSelectedType(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ color: "#022D5E", fontSize: "1rem" }}>
          Flag as {FLAG_TYPES.find((f) => f.value === selectedType)?.label}
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            rows={3}
            size="small"
            label="Comment (optional)"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedType(null)} size="small">
            Cancel
          </Button>
          <Button
            onClick={() => handleSubmit()}
            disabled={submitting}
            variant="contained"
            size="small"
            sx={{ bgcolor: "#D0002B" }}
          >
            Submit Flag
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
