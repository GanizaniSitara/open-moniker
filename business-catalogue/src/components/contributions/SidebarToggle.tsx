"use client";
import { useEffect, useState } from "react";
import { IconButton, Badge } from "@mui/material";
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
      <IconButton
        onClick={() => setOpen(true)}
        size="small"
        sx={{ color: "#005587" }}
      >
        <Badge
          badgeContent={count}
          color="primary"
          max={99}
          sx={{
            "& .MuiBadge-badge": {
              fontSize: "0.65rem",
              height: 16,
              minWidth: 16,
              bgcolor: "#005587",
            },
          }}
        >
          <ChatBubbleOutlineIcon sx={{ fontSize: 20 }} />
        </Badge>
      </IconButton>

      <ContributionsSidebar
        open={open}
        onClose={() => setOpen(false)}
        entityType={entityType}
        entityKey={entityKey}
      />
    </>
  );
}
