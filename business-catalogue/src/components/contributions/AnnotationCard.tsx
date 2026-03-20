"use client";
import { useState } from "react";
import { Box, Typography, Chip, IconButton } from "@mui/material";
import ThumbUpIcon from "@mui/icons-material/ThumbUp";
import ThumbUpOutlinedIcon from "@mui/icons-material/ThumbUpOutlined";
import { upvoteAnnotation, removeUpvote } from "@/lib/contributions-client";
import { useAuthor } from "./AuthorInput";
import AuthorInput from "./AuthorInput";
import type { Annotation } from "@/lib/contributions-types";

const TYPE_STYLES: Record<string, { bg: string; color: string }> = {
  tip: { bg: "#E8F5E9", color: "#2E7D32" },
  warning: { bg: "#FFF3E0", color: "#E65100" },
  context: { bg: "#E3F2FD", color: "#1565C0" },
  usage: { bg: "#F3E5F5", color: "#7B1FA2" },
};

interface AnnotationCardProps {
  annotation: Annotation;
  onVoteChange?: () => void;
}

export default function AnnotationCard({ annotation, onVoteChange }: AnnotationCardProps) {
  const [author, setAuthor] = useAuthor();
  const [showAuthor, setShowAuthor] = useState(false);
  const [voted, setVoted] = useState(false);
  const [count, setCount] = useState(annotation.upvoteCount);
  const style = TYPE_STYLES[annotation.annotationType] || TYPE_STYLES.context;

  const handleVote = async (authorName?: string) => {
    const name = authorName || author;
    if (!name) {
      setShowAuthor(true);
      return;
    }

    if (voted) {
      await removeUpvote(annotation.id, name);
      setCount((c) => c - 1);
      setVoted(false);
    } else {
      await upvoteAnnotation(annotation.id, name);
      setCount((c) => c + 1);
      setVoted(true);
    }
    onVoteChange?.();
  };

  return (
    <>
      <Box
        sx={{
          p: 1.5,
          borderRadius: 1,
          bgcolor: "#f8f9fa",
          border: "1px solid rgba(83,86,90,0.15)",
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
          <Chip
            label={annotation.annotationType}
            size="small"
            sx={{
              bgcolor: style.bg,
              color: style.color,
              fontSize: "0.7rem",
              height: 22,
              fontWeight: 600,
            }}
          />
          <Box sx={{ flexGrow: 1 }} />
          <Typography variant="caption" color="text.secondary">
            {annotation.author} &middot; {new Date(annotation.createdAt).toLocaleDateString()}
          </Typography>
        </Box>
        <Typography variant="body2" sx={{ color: "#53565A", my: 1 }}>
          {annotation.content}
        </Typography>
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
          <IconButton
            size="small"
            onClick={() => handleVote()}
            sx={{ color: voted ? "#789D4A" : "#53565A" }}
          >
            {voted ? <ThumbUpIcon fontSize="small" /> : <ThumbUpOutlinedIcon fontSize="small" />}
          </IconButton>
          <Typography variant="caption" sx={{ color: "#53565A" }}>
            {count}
          </Typography>
        </Box>
      </Box>

      <AuthorInput
        open={showAuthor}
        onClose={() => setShowAuthor(false)}
        onSubmit={(name) => {
          setAuthor(name);
          setShowAuthor(false);
          handleVote(name);
        }}
      />
    </>
  );
}
