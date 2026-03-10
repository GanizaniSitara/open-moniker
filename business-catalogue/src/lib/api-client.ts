/**
 * API client for the Moniker Service.
 * Replaces direct YAML file reading with HTTP calls to the running service.
 */

const API_BASE = process.env.MONIKER_API_URL || "http://localhost:8060";

async function apiFetch<T>(path: string): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, { next: { revalidate: 60 } });
  if (!res.ok) {
    throw new Error(`Moniker API ${res.status}: ${path}`);
  }
  return res.json();
}

// ── Domain types ──

export interface ApiDomain {
  name: string;
  id: number | null;
  display_name: string;
  short_code: string;
  data_category: string;
  color: string;
  owner: string;
  tech_custodian: string;
  business_steward: string;
  confidentiality: string;
  pii: boolean;
  help_channel: string;
  wiki_link: string;
  notes: string;
}

// ── Catalog search types ──

export interface ApiCatalogResult {
  path: string;
  display_name: string;
  description: string;
  status: string;
  has_source_binding: boolean;
  classification: string;
  tags: string[];
}

// ── Model types ──

export interface ApiMonikerLink {
  moniker_pattern: string;
  column_name: string | null;
  notes: string | null;
}

export interface ApiModelOwnership {
  methodology_owner: string | null;
  business_steward: string | null;
  support_channel: string | null;
}

export interface ApiModel {
  path: string;
  display_name: string;
  description: string;
  formula: string | null;
  unit: string | null;
  data_type: string;
  ownership: ApiModelOwnership | null;
  documentation_url: string | null;
  methodology_url: string | null;
  appears_in: ApiMonikerLink[];
  semantic_tags: string[];
  tags: string[];
}

// ── Describe types ──

export interface ApiDescribeColumn {
  name: string;
  type: string;
  description: string;
  semantic_type?: string;
  primary_key?: boolean;
  foreign_key?: string;
}

export interface ApiDescribeSchema {
  columns: ApiDescribeColumn[];
  semantic_tags: string[];
  use_cases: string[];
}

export interface ApiDescribeModel {
  path: string;
  display_name: string;
  description: string;
  unit: string | null;
  formula: string | null;
}

export interface ApiDescribeResponse {
  path: string;
  display_name: string | null;
  description: string | null;
  ownership: Record<string, unknown>;
  has_source_binding: boolean;
  source_type: string | null;
  classification: string | null;
  tags: string[];
  schema: ApiDescribeSchema | null;
  documentation: Record<string, string | null> | null;
  models: ApiDescribeModel[] | null;
}

// ── Fetch functions ──

export const fetchDomains = () =>
  apiFetch<{ domains: ApiDomain[]; count: number }>("/domains");

export const fetchDomainDetail = (name: string) =>
  apiFetch<{ domain: ApiDomain; moniker_paths: string[]; moniker_count: number }>(
    `/domains/${encodeURIComponent(name)}`
  );

export const fetchCatalogSearch = (q = "", limit = 500) =>
  apiFetch<{ results: ApiCatalogResult[]; query: string; total_results: number }>(
    `/catalog/search?q=${encodeURIComponent(q)}&limit=${limit}`
  );

export const fetchModels = () =>
  apiFetch<{ models: ApiModel[]; count: number }>("/models");

export const fetchModelDetail = (path: string) =>
  apiFetch<{ model: ApiModel; moniker_patterns: string[]; moniker_count: number }>(
    `/models/${path}`
  );

export const fetchDescribe = (path: string) =>
  apiFetch<ApiDescribeResponse>(`/describe/${path}`);
