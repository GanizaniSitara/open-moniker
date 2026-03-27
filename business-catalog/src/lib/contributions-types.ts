// ── Flag ──────────────────────────────────────────────────

export type FlagType = "outdated" | "incorrect" | "missing" | "unclear";
export type FlagStatus = "open" | "acknowledged" | "resolved" | "dismissed";

export interface Flag {
  id: string;
  entityType: string;
  entityKey: string;
  flagType: FlagType;
  comment: string | null;
  author: string;
  status: FlagStatus;
  resolvedBy: string | null;
  resolvedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface CreateFlagRequest {
  entityType: string;
  entityKey: string;
  flagType: FlagType;
  comment?: string;
  author: string;
}

export interface FlagSummary {
  total: number;
  byType: Record<FlagType, number>;
}

// ── Suggestion ───────────────────────────────────────────

export type SuggestionStatus = "pending" | "approved" | "rejected";

export interface Suggestion {
  id: string;
  entityType: string;
  entityKey: string;
  fieldName: string;
  currentValue: string | null;
  proposedValue: string;
  reason: string | null;
  author: string;
  status: SuggestionStatus;
  reviewedBy: string | null;
  reviewComment: string | null;
  reviewedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface CreateSuggestionRequest {
  entityType: string;
  entityKey: string;
  fieldName: string;
  currentValue?: string;
  proposedValue: string;
  reason?: string;
  author: string;
}

// ── Annotation ───────────────────────────────────────────

export type AnnotationType = "tip" | "warning" | "context" | "usage";

export interface Annotation {
  id: string;
  entityType: string;
  entityKey: string;
  annotationType: AnnotationType;
  content: string;
  author: string;
  upvoteCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface CreateAnnotationRequest {
  entityType: string;
  entityKey: string;
  annotationType: AnnotationType;
  content: string;
  author: string;
}

// ── Discussion ───────────────────────────────────────────

export interface Discussion {
  id: string;
  entityType: string;
  entityKey: string;
  title: string;
  author: string;
  replyCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface Reply {
  id: string;
  discussionId: string;
  parentReplyId: string | null;
  content: string;
  author: string;
  createdAt: string;
  updatedAt: string;
}

export interface DiscussionDetail {
  id: string;
  entityType: string;
  entityKey: string;
  title: string;
  author: string;
  createdAt: string;
  updatedAt: string;
  replies: Reply[];
}

export interface CreateDiscussionRequest {
  entityType: string;
  entityKey: string;
  title: string;
  author: string;
}

export interface CreateReplyRequest {
  content: string;
  author: string;
  parentReplyId?: string;
}

// ── Helpful ──────────────────────────────────────────────

export interface HelpfulSummary {
  helpful: number;
  notHelpful: number;
  total: number;
}

// ── Activity ─────────────────────────────────────────────

export interface ActivitySummary {
  flags: number;
  suggestions: number;
  annotations: number;
  discussions: number;
  total: number;
}
