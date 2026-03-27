import type {
  Flag,
  FlagSummary,
  CreateFlagRequest,
  Annotation,
  CreateAnnotationRequest,
  Suggestion,
  CreateSuggestionRequest,
  Discussion,
  DiscussionDetail,
  CreateDiscussionRequest,
  CreateReplyRequest,
  Reply,
  ActivitySummary,
  HelpfulSummary,
} from "./contributions-types";

export function isContributionsEnabled(): boolean {
  return process.env.NEXT_PUBLIC_CONTRIBUTIONS_ENABLED === "true";
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api/contributions${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `API error ${res.status}`);
  }
  return res.json();
}

// ── Flags ────────────────────────────────────────────────

export async function createFlag(data: CreateFlagRequest): Promise<Flag> {
  return api("/flags", { method: "POST", body: JSON.stringify(data) });
}

export async function fetchFlags(entityType: string, entityKey: string): Promise<Flag[]> {
  return api(`/flags?entityType=${encodeURIComponent(entityType)}&entityKey=${encodeURIComponent(entityKey)}`);
}

export async function fetchFlagSummary(entityType: string, entityKey: string): Promise<FlagSummary> {
  return api(`/flags/summary?entityType=${encodeURIComponent(entityType)}&entityKey=${encodeURIComponent(entityKey)}`);
}

export async function updateFlagStatus(id: string, status: string, resolvedBy?: string): Promise<Flag> {
  return api(`/flags/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status, resolvedBy }),
  });
}

// ── Annotations ──────────────────────────────────────────

export async function createAnnotation(data: CreateAnnotationRequest): Promise<Annotation> {
  return api("/annotations", { method: "POST", body: JSON.stringify(data) });
}

export async function fetchAnnotations(entityType: string, entityKey: string): Promise<Annotation[]> {
  return api(`/annotations?entityType=${encodeURIComponent(entityType)}&entityKey=${encodeURIComponent(entityKey)}`);
}

export async function upvoteAnnotation(id: string, voter: string): Promise<void> {
  await api(`/annotations/${id}/upvote`, {
    method: "POST",
    body: JSON.stringify({ voter }),
  });
}

export async function removeUpvote(id: string, voter: string): Promise<void> {
  await api(`/annotations/${id}/upvote`, {
    method: "DELETE",
    body: JSON.stringify({ voter }),
  });
}

// ── Suggestions ──────────────────────────────────────────

export async function createSuggestion(data: CreateSuggestionRequest): Promise<Suggestion> {
  return api("/suggestions", { method: "POST", body: JSON.stringify(data) });
}

export async function fetchSuggestions(entityType: string, entityKey: string): Promise<Suggestion[]> {
  return api(`/suggestions?entityType=${encodeURIComponent(entityType)}&entityKey=${encodeURIComponent(entityKey)}`);
}

// ── Discussions ──────────────────────────────────────────

export async function createDiscussion(data: CreateDiscussionRequest): Promise<Discussion> {
  return api("/discussions", { method: "POST", body: JSON.stringify(data) });
}

export async function fetchDiscussions(entityType: string, entityKey: string): Promise<Discussion[]> {
  return api(`/discussions?entityType=${encodeURIComponent(entityType)}&entityKey=${encodeURIComponent(entityKey)}`);
}

export async function fetchDiscussion(id: string): Promise<DiscussionDetail> {
  return api(`/discussions/${id}`);
}

export async function addReply(discussionId: string, data: CreateReplyRequest): Promise<Reply> {
  return api(`/discussions/${discussionId}/replies`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ── Helpful Votes ───────────────────────────────────────

export async function submitHelpfulVote(data: {
  entityType: string;
  entityKey: string;
  helpful: boolean;
  comment?: string;
  author?: string;
}): Promise<void> {
  await api("/helpful", { method: "POST", body: JSON.stringify(data) });
}

export async function fetchHelpfulSummary(entityType: string, entityKey: string): Promise<HelpfulSummary> {
  return api(`/helpful?entityType=${encodeURIComponent(entityType)}&entityKey=${encodeURIComponent(entityKey)}`);
}

// ── Activity ─────────────────────────────────────────────

export async function fetchActivity(entityType: string, entityKey: string): Promise<ActivitySummary> {
  return api(`/activity?entityType=${encodeURIComponent(entityType)}&entityKey=${encodeURIComponent(entityKey)}`);
}
