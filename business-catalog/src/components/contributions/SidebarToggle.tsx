"use client";
import { useEffect, useState } from "react";
import { Box, Typography } from "@mui/material";
import ChatBubbleOutlineIcon from "@mui/icons-material/ChatBubbleOutline";
import { isContributionsEnabled, fetchActivity } from "@/lib/contributions-client";
import ContributionsSidebar from "./ContributionsSidebar";

interface SidebarToggleProps {
  entityType: string;
  entityKey: string;
}

export default function SidebarToggle({ entityType, entityKey }: SidebarToggleProps) {
  const [open, setOpen] = useState(false);
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (!isContributionsEnabled()) return;
    fetchActivity(entityType, entityKey)
      .then((a) => setCount(a.total))
      .catch(() => {});
  }, [entityType, entityKey]);

  if (!isContributionsEnabled()) return null;

  return (
    <>
      <Box
        onClick={() => setOpen(true)}
        sx={{
          display: "inline-flex",
          alignItems: "center",
          gap: 0.5,
          cursor: "pointer",
          color: "#005587",
          "&:hover": { opacity: 0.7 },
        }}
      >
        <ChatBubbleOutlineIcon sx={{ fontSize: 18 }} />
        <Typography variant="body2" sx={{ fontWeight: 500, fontSize: "0.8rem" }}>
          {count > 0 ? `Community · ${count}` : "Community"}
        </Typography>
      </Box>

      <ContributionsSidebar
        open={open}
        onClose={() => setOpen(false)}
        entityType={entityType}
        entityKey={entityKey}
      />
    </>
  );
}
