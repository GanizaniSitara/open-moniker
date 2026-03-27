"use client";
import { useEffect, useState, useCallback } from "react";
import {
  Box,
  Typography,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Collapse,
  IconButton,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import ChatBubbleOutlineIcon from "@mui/icons-material/ChatBubbleOutline";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import AuthorInput, { useAuthor } from "./AuthorInput";
import {
  fetchDiscussions,
  fetchDiscussion,
  createDiscussion,
  addReply,
} from "@/lib/contributions-client";
import type { Discussion, DiscussionDetail } from "@/lib/contributions-types";

interface DiscussionListProps {
  entityType: string;
  entityKey: string;
}

export default function DiscussionList({ entityType, entityKey }: DiscussionListProps) {
  const [author, setAuthor] = useAuthor();
  const [discussions, setDiscussions] = useState<Discussion[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [showAuthor, setShowAuthor] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<DiscussionDetail | null>(null);
  const [replyText, setReplyText] = useState("");
  const [pendingAction, setPendingAction] = useState<"create" | "reply" | null>(null);

  const load = useCallback(() => {
    fetchDiscussions(entityType, entityKey).then(setDiscussions).catch(() => {});
  }, [entityType, entityKey]);

  useEffect(() => { load(); }, [load]);

  const handleExpand = async (id: string) => {
    if (expandedId === id) {
      setExpandedId(null);
      setDetail(null);
      return;
    }
    setExpandedId(id);
    try {
      const d = await fetchDiscussion(id);
      setDetail(d);
    } catch {
      // ignore
    }
  };

  const handleCreate = async (authorName?: string) => {
    const name = authorName || author;
    if (!name) {
      setPendingAction("create");
      setShowAuthor(true);
      return;
    }
    if (!newTitle.trim()) return;

    setSubmitting(true);
    try {
      await createDiscussion({ entityType, entityKey, title: newTitle.trim(), author: name });
      setNewTitle("");
      setShowCreate(false);
      load();
    } finally {
      setSubmitting(false);
    }
  };

  const handleReply = async (authorName?: string) => {
    const name = authorName || author;
    if (!name) {
      setPendingAction("reply");
      setShowAuthor(true);
      return;
    }
    if (!expandedId || !replyText.trim()) return;

    setSubmitting(true);
    try {
      await addReply(expandedId, { content: replyText.trim(), author: name });
      setReplyText("");
      const d = await fetchDiscussion(expandedId);
      setDetail(d);
      load();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", mb: 1.5 }}>
        <Typography variant="subtitle2" sx={{ flexGrow: 1, color: "#022D5E" }}>
          Discussions ({discussions.length})
        </Typography>
        <Button
          size="small"
          startIcon={<AddIcon />}
          onClick={() => setShowCreate(true)}
          sx={{ textTransform: "none", fontSize: "0.8rem", color: "#005587" }}
        >
          Start Discussion
        </Button>
      </Box>

      {discussions.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          No discussions yet. Start one!
        </Typography>
      ) : (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
          {discussions.map((d) => (
            <Box key={d.id}>
              <Box
                onClick={() => handleExpand(d.id)}
                sx={{
                  p: 1.5,
                  borderRadius: 1,
                  bgcolor: expandedId === d.id ? "#EBF5FB" : "#f8f9fa",
                  border: "1px solid rgba(83,86,90,0.15)",
                  cursor: "pointer",
                  "&:hover": { bgcolor: "#EBF5FB" },
                }}
              >
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <Typography variant="subtitle2" sx={{ fontSize: "0.85rem", color: "#022D5E", flexGrow: 1 }}>
                    {d.title}
                  </Typography>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                    <ChatBubbleOutlineIcon sx={{ fontSize: 14, color: "#9CA3AF" }} />
                    <Typography variant="caption" color="text.secondary">
                      {d.replyCount}
                    </Typography>
                  </Box>
                  <IconButton size="small">
                    {expandedId === d.id ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
                  </IconButton>
                </Box>
                <Typography variant="caption" color="text.secondary">
                  {d.author} &middot; {new Date(d.updatedAt).toLocaleDateString()}
                </Typography>
              </Box>

              <Collapse in={expandedId === d.id}>
                <Box sx={{ pl: 2, pr: 1, py: 1, borderLeft: "2px solid #005587", ml: 1.5, mt: 0.5 }}>
                  {detail && detail.id === d.id ? (
                    <>
                      {detail.replies.length === 0 ? (
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          No replies yet.
                        </Typography>
                      ) : (
                        detail.replies.map((r) => (
                          <Box key={r.id} sx={{ mb: 1, p: 1, bgcolor: "#f8f9fa", borderRadius: 1 }}>
                            <Typography variant="body2" sx={{ fontSize: "0.8rem" }}>
                              {r.content}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {r.author} &middot; {new Date(r.createdAt).toLocaleDateString()}
                            </Typography>
                          </Box>
                        ))
                      )}
                      <Box sx={{ display: "flex", gap: 1, mt: 1 }}>
                        <TextField
                          size="small"
                          placeholder="Write a reply..."
                          value={replyText}
                          onChange={(e) => setReplyText(e.target.value)}
                          fullWidth
                          onKeyDown={(e) => {
                            if (e.key === "Enter" && !e.shiftKey && replyText.trim()) {
                              e.preventDefault();
                              handleReply();
                            }
                          }}
                        />
                        <Button
                          size="small"
                          variant="contained"
                          disabled={submitting || !replyText.trim()}
                          onClick={() => handleReply()}
                          sx={{ bgcolor: "#005587", textTransform: "none", minWidth: 60 }}
                        >
                          Reply
                        </Button>
                      </Box>
                    </>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      Loading...
                    </Typography>
                  )}
                </Box>
              </Collapse>
            </Box>
          ))}
        </Box>
      )}

      <Dialog open={showCreate} onClose={() => setShowCreate(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ color: "#022D5E", fontSize: "1rem" }}>
          Start a Discussion
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            size="small"
            label="Discussion title"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            sx={{ mt: 1 }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && newTitle.trim()) {
                handleCreate();
              }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCreate(false)} size="small">Cancel</Button>
          <Button
            onClick={() => handleCreate()}
            disabled={submitting || !newTitle.trim()}
            variant="contained"
            size="small"
            sx={{ bgcolor: "#005587" }}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>

      <AuthorInput
        open={showAuthor}
        onClose={() => { setShowAuthor(false); setPendingAction(null); }}
        onSubmit={(name) => {
          setAuthor(name);
          setShowAuthor(false);
          if (pendingAction === "create") handleCreate(name);
          else if (pendingAction === "reply") handleReply(name);
          setPendingAction(null);
        }}
      />
    </Box>
  );
}
