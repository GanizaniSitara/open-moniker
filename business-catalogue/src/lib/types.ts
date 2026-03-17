// Domain (from domains.yaml)
export interface Domain {
  key: string;
  id: number;
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

// Column in a dataset schema
export interface Column {
  name: string;
  type: string;
  description?: string;
  semantic_type?: string;
  primary_key?: boolean;
  foreign_key?: string;
}

// Schema definition
export interface Schema {
  columns: Column[];
  semantic_tags?: string[];
  use_cases?: string[];
}

// Source binding configuration
export interface SourceBinding {
  type: string;
  config: Record<string, unknown>;
}

// Ownership information
export interface Ownership {
  accountable_owner?: string;
  data_specialist?: string;
  support_channel?: string;
  adop?: string;
  ads?: string;
  adal?: string;
}

// Documentation links
export interface Documentation {
  glossary?: string;
  runbook?: string;
  data_dictionary?: string;
  onboarding?: string;
  additional?: Record<string, string>;
}

// Access policy
export interface AccessPolicy {
  min_filters?: number;
  blocked_patterns?: string[];
  max_rows_warn?: number;
  denial_message?: string;
}

// Dataset (from catalog.yaml)
export interface Dataset {
  key: string;
  display_name: string;
  description?: string;
  ownership?: Ownership;
  documentation?: Documentation;
  source_binding?: SourceBinding;
  schema?: Schema;
  classification?: string;
  access_policy?: AccessPolicy;
  semantic_tags?: string[];
  vendor?: string;
  // Computed fields
  domainKey?: string;
  isContainer: boolean;
}

// Field alias (alternative name)
export interface FieldAlias {
  name: string;
  type: string;  // abbreviation, common_name, system_name, legacy_name, vendor_name
  context?: string;
}

// Model link (where a model appears)
export interface MonikerLink {
  moniker_pattern: string;
  column_name?: string;
  notes?: string;
}

// Model ownership
export interface ModelOwnership {
  methodology_owner?: string;
  business_steward?: string;
  support_channel?: string;
}

// Business model (from models.yaml)
export interface Model {
  key: string;
  display_name: string;
  description?: string;
  formula?: string;
  unit?: string;
  data_type?: string;
  documentation_url?: string;
  methodology_url?: string;
  wiki_link?: string;
  ownership?: ModelOwnership;
  appears_in?: MonikerLink[];
  aliases?: FieldAlias[];
  semantic_tags?: string[];
  // Computed
  isContainer: boolean;
}

// Search result
export interface SearchResult {
  type: "domain" | "dataset" | "model";
  key: string;
  display_name: string;
  description?: string;
  url: string;
}
