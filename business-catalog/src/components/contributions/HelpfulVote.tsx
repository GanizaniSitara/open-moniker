"use client";
import { useState, useEffect } from "react";
import { Box, Typography, IconButton, Chip } from "@mui/material";
import ThumbUpIcon from "@mui/icons-material/ThumbUp";
import ThumbUpOutlinedIcon from "@mui/icons-material/ThumbUpOutlined";
import ThumbDownIcon from "@mui/icons-material/ThumbDown";
import ThumbDownOutlinedIcon from "@mui/icons-material/ThumbDownOutlined";
import { isContributionsEnabled, submitHelpfulVote } from "@/lib/contributions-client";

const FOLLOW_UP_OPTIONS = ["Outdated", "Incorrect", "Missing", "Unclear"] as const;

interface HelpfulVoteProps {
  entityType: string;
  entityKey: string;
}

export default function HelpfulVote({ entityType, entityKey }: HelpfulVoteProps) {
  const [vote, setVote] = useState<"yes" | "no" | null>(null);
  const [followUp, setFollowUp] = useState<string | null>(null);
  const [alreadyVoted, setAlreadyVoted] = useState(false);

  const storageKey = `helpful_vote_${entityType}_${entityKey}`;

  useEffect(() => {
    if (!isContributionsEnabled()) return;
    const stored = localStorage.getItem(storageKey);
    if (stored) setAlreadyVoted(true);
  }, [storageKey]);

  if (!isContributionsEnabled() || alreadyVoted) return null;

  const handleVote = async (helpful: boolean) => {
    const choice = helpful ? "yes" : "no";
    setVote(choice);
    if (helpful) {
      await submitHelpfulVote({ entityType, entityKey, helpful: true }).catch(() => {});
      localStorage.setItem(storageKey, "yes");
    }
  };

  const handleFollowUp = async (option: string) => {
    setFollowUp(option);
    await submitHelpfulVote({
      entityType,
      entityKey,
      helpful: false,
      comment: option,
    }).catch(() => {});
    localStorage.setItem(storageKey, "no");
  };

  return (
    <Box
      sx={{
        mt: 4,
        py: 3,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        borderTop: "1px solid rgba(83,86,90,0.15)",
      }}
    >
      {vote === null && (
        <>
          <Typography variant="body2" sx={{ color: "#53565A", mb: 1 }}>
            Was this page helpful?
          </Typography>
          <Box sx={{ display: "flex", gap: 1 }}>
            <IconButton
              onClick={() => handleVote(true)}
              sx={{ color: "#009639" }}
            >
              <ThumbUpOutlinedIcon />
            </IconButton>
            <IconButton
              onClick={() => handleVote(false)}
              sx={{ color: "#D0002B" }}
            >
              <ThumbDownOutlinedIcon />
            </IconButton>
          </Box>
        </>
      )}

      {vote === "yes" && (
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <ThumbUpIcon sx={{ color: "#009639", fontSize: 20 }} />
          <Typography variant="body2" sx={{ color: "#009639" }}>
            Thank you for your feedback!
          </Typography>
        </Box>
      )}

      {vote === "no" && !followUp && (
        <>
          <Typography variant="body2" sx={{ color: "#53565A", mb: 1.5 }}>
            What was the issue?
          </Typography>
          <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", justifyContent: "center" }}>
            {FOLLOW_UP_OPTIONS.map((option) => (
              <Chip
                key={option}
                label={option}
                variant="outlined"
                clickable
                onClick={() => handleFollowUp(option)}
                sx={{
                  borderColor: "#D0002B",
                  color: "#D0002B",
                  "&:hover": { bgcolor: "#FFEBEE" },
                }}
              />
            ))}
          </Box>
        </>
      )}

      {vote === "no" && followUp && (
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <ThumbDownIcon sx={{ color: "#D0002B", fontSize: 20 }} />
          <Typography variant="body2" sx={{ color: "#53565A" }}>
            Thank you for your feedback!
          </Typography>
        </Box>
      )}
    </Box>
  );
}
