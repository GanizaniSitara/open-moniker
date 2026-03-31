"use client";
import { useState, useCallback } from "react";
import { Drawer, Box, Typography, Tabs, Tab, IconButton } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import FlagButton from "./FlagButton";
import FlagList from "./FlagList";
import AnnotationList from "./AnnotationList";
import SuggestionList from "./SuggestionList";
import DiscussionList from "./DiscussionList";
import { fetchFlags } from "@/lib/contributions-client";
import type { Flag } from "@/lib/contributions-types";
import { useEffect } from "react";

interface ContributionsSidebarProps {
  open: boolean;
  onClose: () => void;
  entityType: string;
  entityKey: string;
}

export default function ContributionsSidebar({
  open,
  onClose,
  entityType,
  entityKey,
}: ContributionsSidebarProps) {
  const [tab, setTab] = useState(0);
  const [flags, setFlags] = useState<Flag[]>([]);

  const loadFlags = useCallback(() => {
    fetchFlags(entityType, entityKey).then(setFlags).catch(() => {});
  }, [entityType, entityKey]);

  useEffect(() => {
    if (open) loadFlags();
  }, [open, loadFlags]);

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      variant="temporary"
      PaperProps={{ sx: { width: 420, maxWidth: "100vw" } }}
    >
      <Box sx={{ display: "flex", alignItems: "center", px: 2, pt: 2, pb: 1 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600, color: "#022D5E", flexGrow: 1 }}>
          Community
        </Typography>
        <FlagButton entityType={entityType} entityKey={entityKey} onFlagged={loadFlags} />
        <IconButton onClick={onClose} size="small" sx={{ ml: 0.5 }}>
          <CloseIcon fontSize="small" />
        </IconButton>
      </Box>

      <Tabs
        value={tab}
        onChange={(_, v) => setTab(v)}
        variant="fullWidth"
        sx={{
          minHeight: 36,
          borderBottom: "1px solid rgba(83,86,90,0.2)",
          "& .MuiTab-root": {
            minHeight: 36,
            textTransform: "none",
            fontSize: "0.8rem",
            py: 0,
          },
        }}
      >
        <Tab label={`Flags (${flags.length})`} />
        <Tab label="Annotations" />
        <Tab label="Suggestions" />
        <Tab label="Discussions" />
      </Tabs>

      <Box sx={{ p: 2, overflow: "auto", flexGrow: 1 }}>
        {tab === 0 && <FlagList flags={flags} />}
        {tab === 1 && <AnnotationList entityType={entityType} entityKey={entityKey} />}
        {tab === 2 && <SuggestionList entityType={entityType} entityKey={entityKey} />}
        {tab === 3 && <DiscussionList entityType={entityType} entityKey={entityKey} />}
      </Box>
    </Drawer>
  );
}
