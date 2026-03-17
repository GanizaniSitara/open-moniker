/**
 * API client for the Moniker Service.
 * All catalogue data is fetched from the service API rather than YAML files.
 */

const API_BASE = process.env.MONIKER_API_URL || "http://localhost:8060";

/** Convert slash-separated URL path to dot-separated moniker path */
export function toDotPath(slashPath: string): string {
  return slashPath.replace(/\//g, ".");
}

/** Convert dot-separated moniker path to slash-separated URL path */
export function toSlashPath(dotPath: string): string {
  return dotPath.replace(/\./g, "/");
}

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { next: { revalidate: 30 } });
  if (!res.ok) {
    throw new Error(`Moniker API ${path}: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// ── Domain types & fetchers ──────────────────────────────────────────

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

interface DomainListResponse {
  domains: ApiDomain[];
  count: number;
}

interface DomainWithMonikersResponse {
  domain: ApiDomain;
  moniker_paths: string[];
  moniker_count: number;
}

export async function fetchDomains(): Promise<DomainListResponse> {
  return apiFetch("/domains");
}

export async function fetchDomain(name: string): Promise<DomainWithMonikersResponse> {
  return apiFetch(`/domains/${encodeURIComponent(name)}`);
}

// ── Node (dataset) types & fetchers ──────────────────────────────────

export interface ApiOwnership {
  accountable_owner?: string | null;
  data_specialist?: string | null;
  support_channel?: string | null;
  adop?: string | null;
  ads?: string | null;
  adal?: string | null;
}

export interface ApiSourceBinding {
  type: string;
  config: Record<string, unknown>;
  allowed_operations?: string[] | null;
  schema?: Record<string, unknown> | null;
  read_only: boolean;
}

export interface ApiNode {
  path: string;
  display_name: string;
  description: string;
  domain: string | null;
  resolved_domain: string | null;
  vendor: string | null;
  ownership: ApiOwnership | null;
  source_binding: ApiSourceBinding | null;
  classification: string;
  maturity: string;
  tags: string[];
  is_leaf: boolean;
  status: string;
}

interface NodeListResponse {
  nodes: ApiNode[];
  total: number;
}

interface ResolvedOwnership {
  accountable_owner?: string | null;
  accountable_owner_source?: string | null;
  data_specialist?: string | null;
  data_specialist_source?: string | null;
  support_channel?: string | null;
  support_channel_source?: string | null;
  adop?: string | null;
  adop_source?: string | null;
  ads?: string | null;
  ads_source?: string | null;
  adal?: string | null;
  adal_source?: string | null;
}

interface NodeWithOwnershipResponse {
  node: ApiNode;
  resolved_ownership: ResolvedOwnership;
}

export async function fetchNodes(): Promise<NodeListResponse> {
  return apiFetch("/config/nodes");
}

export async function fetchNode(path: string): Promise<NodeWithOwnershipResponse> {
  return apiFetch(`/config/nodes/${path}`);
}

// ── Describe (rich metadata for a single dataset) ────────────────────

export interface ApiColumn {
  name: string;
  type: string;
  description?: string;
  semantic_type?: string | null;
  example?: string | null;
  nullable?: boolean;
  primary_key?: boolean;
  foreign_key?: string | null;
}

export interface ApiSchema {
  description?: string;
  semantic_tags?: string[];
  granularity?: string | null;
  primary_key?: string[];
  columns?: ApiColumn[];
  use_cases?: string[];
  related_monikers?: string[];
}

export interface ApiDocumentation {
  glossary?: string | null;
  runbook?: string | null;
  onboarding?: string | null;
  data_dictionary?: string | null;
  api_docs?: string | null;
  architecture?: string | null;
  changelog?: string | null;
  contact?: string | null;
  additional?: Record<string, string>;
}

export interface ApiAccessPolicy {
  min_filters?: number | null;
  blocked_patterns?: string[];
  max_rows_warn?: number | null;
  denial_message?: string | null;
}

export interface ApiDescribeModel {
  path: string;
  display_name: string;
  description?: string;
  unit?: string | null;
  formula?: string | null;
  documentation_url?: string | null;
}

export interface DescribeResponse {
  path: string;
  display_name: string | null;
  description: string | null;
  technical_description?: string | null;
  asset_class?: string | null;
  update_frequency?: string | null;
  ownership: ResolvedOwnership;
  has_source_binding: boolean;
  source_type: string | null;
  vendor: string | null;
  classification: string | null;
  maturity: string | null;
  tags: string[];
  schema: ApiSchema | null;
  documentation: ApiDocumentation | null;
  access_policy?: ApiAccessPolicy | null;
  models: ApiDescribeModel[] | null;
}

export async function fetchDescribe(path: string): Promise<DescribeResponse> {
  return apiFetch(`/describe/${path}`);
}

// ── Model (business model) types & fetchers ──────────────────────────

export interface ApiFieldAlias {
  name: string;
  type: string;
  context?: string | null;
}

export interface ApiMonikerLink {
  moniker_pattern: string;
  column_name?: string | null;
  notes?: string | null;
}

export interface ApiModelOwnership {
  methodology_owner?: string | null;
  business_steward?: string | null;
  support_channel?: string | null;
}

export interface ApiModel {
  path: string;
  display_name: string;
  description: string;
  formula?: string | null;
  unit?: string | null;
  data_type?: string;
  ownership?: ApiModelOwnership | null;
  documentation_url?: string | null;
  methodology_url?: string | null;
  wiki_link?: string | null;
  appears_in: ApiMonikerLink[];
  aliases: ApiFieldAlias[];
  semantic_tags: string[];
  tags: string[];
}

interface ModelListResponse {
  models: ApiModel[];
  count: number;
}

interface ModelWithMonikersResponse {
  model: ApiModel;
  moniker_patterns: string[];
  moniker_count: number;
}

interface ModelsForMonikerResponse {
  moniker_path: string;
  models: ApiDescribeModel[];
  count: number;
}

export async function fetchModels(): Promise<ModelListResponse> {
  return apiFetch("/models");
}

export async function fetchModel(path: string): Promise<ModelWithMonikersResponse> {
  return apiFetch(`/models/${path}`);
}

export async function fetchModelsForMoniker(path: string): Promise<ModelsForMonikerResponse> {
  return apiFetch(`/models/for-moniker/${path}`);
}

// ── Application types & fetchers ──────────────────────────────────────

export interface ApiApplication {
  key: string;
  display_name: string;
  description: string;
  category: string;
  color: string;
  status: string;
  owner: string;
  tech_lead: string;
  support_channel: string;
  datasets: string[];
  fields: string[];
  documentation_url: string;
  wiki_link: string;
}

interface ApplicationListResponse {
  applications: ApiApplication[];
  count: number;
}

interface ApplicationDetailResponse {
  application: ApiApplication;
  dataset_count: number;
  field_count: number;
}

interface ApplicationsForDatasetResponse {
  dataset_path: string;
  applications: ApiApplication[];
  count: number;
}

export async function fetchApplications(): Promise<ApplicationListResponse> {
  return apiFetch("/applications");
}

export async function fetchApplication(key: string): Promise<ApplicationDetailResponse> {
  return apiFetch(`/applications/${encodeURIComponent(key)}`);
}

export async function fetchApplicationsForDataset(path: string): Promise<ApplicationsForDatasetResponse> {
  return apiFetch(`/applications/for-dataset/${path}`);
}

// ── Search ───────────────────────────────────────────────────────────

interface CatalogSearchResult {
  path: string;
  display_name: string;
  description?: string;
  score: number;
}

interface CatalogSearchResponse {
  results: CatalogSearchResult[];
  query: string;
  total_results: number;
}

export async function fetchCatalogSearch(q: string): Promise<CatalogSearchResponse> {
  return apiFetch(`/catalog/search?q=${encodeURIComponent(q)}`);
}

// ── Tree (catalog hierarchy) ─────────────────────────────────────────

export interface ApiTreeNode {
  path: string;
  name: string;
  children: ApiTreeNode[];
  description: string | null;
  domain: string | null;
  resolved_domain: string | null;
  vendor: string | null;
  has_source_binding: boolean;
  source_type: string | null;
}

export async function fetchTree(depth?: number): Promise<ApiTreeNode[]> {
  const qs = depth != null ? `?depth=${depth}` : "";
  return apiFetch(`/tree${qs}`);
}
