"use client";
import { useEffect, useState } from "react";
import { Box, Tooltip } from "@mui/material";
import { isContributionsEnabled, fetchFlagSummary } from "@/lib/contributions-client";
import type { FlagSummary } from "@/lib/contributions-types";

interface TrustIndicatorProps {
  entityType: string;
  entityKey: string;
}

export default function TrustIndicator({ entityType, entityKey }: TrustIndicatorProps) {
  const [summary, setSummary] = useState<FlagSummary | null>(null);

  useEffect(() => {
    if (!isContributionsEnabled()) return;
    fetchFlagSummary(entityType, entityKey).then(setSummary).catch(() => {});
  }, [entityType, entityKey]);

  if (!isContributionsEnabled()) return null;

  let color = "#009639"; // green — no flags
  let label = "No issues reported";

  if (summary && summary.total > 0) {
    const hasIncorrect = (summary.byType.incorrect || 0) > 0;
    if (hasIncorrect) {
      color = "#D0002B"; // red
      label = `${summary.total} flag${summary.total === 1 ? "" : "s"} — includes incorrect`;
    } else {
      color = "#FFD100"; // yellow
      label = `${summary.total} flag${summary.total === 1 ? "" : "s"} reported`;
    }
  }

  return (
    <Tooltip title={label} arrow>
      <Box
        sx={{
          width: 12,
          height: 12,
          borderRadius: "50%",
          bgcolor: color,
          flexShrink: 0,
        }}
      />
    </Tooltip>
  );
}
