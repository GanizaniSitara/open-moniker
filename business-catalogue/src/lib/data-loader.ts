/**
 * Catalog data loader — fetches from Moniker Service API endpoints
 * instead of reading YAML files directly.
 */

import type { Domain, Dataset, Model } from "./types";
import { catalogKeyToDomain, patternMatches } from "./domain-mapping";
import {
  fetchDomains,
  fetchCatalogSearch,
  fetchModels,
  type ApiDomain,
  type ApiCatalogResult,
  type ApiModel,
} from "./api-client";

export interface CatalogData {
  domains: Domain[];
  datasets: Dataset[];
  models: Model[];
  // Indexes
  domainByKey: Map<string, Domain>;
  datasetByKey: Map<string, Dataset>;
  modelByKey: Map<string, Model>;
  datasetsByDomain: Map<string, Dataset[]>;
  modelsForDataset: Map<string, Model[]>;
  datasetsForModel: Map<string, { dataset: Dataset; columnName?: string; notes?: string }[]>;
}

// ── Mappers: API response → TypeScript types ──

function mapDomain(api: ApiDomain): Domain {
  return {
    key: api.name,
    id: api.id || 0,
    display_name: api.display_name || api.name,
    short_code: api.short_code || "",
    data_category: api.data_category || "",
    color: api.color || "#666",
    owner: api.owner || "",
    tech_custodian: api.tech_custodian || "",
    business_steward: api.business_steward || "",
    confidentiality: api.confidentiality || "internal",
    pii: api.pii || false,
    help_channel: api.help_channel || "",
    wiki_link: api.wiki_link || "",
    notes: api.notes || "",
  };
}

function mapDataset(api: ApiCatalogResult, domainKeys: string[]): Dataset {
  return {
    key: api.path,
    display_name: api.display_name || api.path,
    description: api.description || undefined,
    classification: api.classification || undefined,
    semantic_tags: api.tags,
    domainKey: catalogKeyToDomain(api.path, domainKeys) || undefined,
    isContainer: !api.has_source_binding,
  };
}

function mapModel(api: ApiModel): Model {
  return {
    key: api.path,
    display_name: api.display_name || api.path,
    description: api.description || undefined,
    formula: api.formula || undefined,
    unit: api.unit || undefined,
    data_type: api.data_type || undefined,
    documentation_url: api.documentation_url || undefined,
    methodology_url: api.methodology_url || undefined,
    ownership: api.ownership
      ? {
          methodology_owner: api.ownership.methodology_owner || undefined,
          business_steward: api.ownership.business_steward || undefined,
          support_channel: api.ownership.support_channel || undefined,
        }
      : undefined,
    appears_in: api.appears_in?.map((link) => ({
      moniker_pattern: link.moniker_pattern,
      column_name: link.column_name || undefined,
      notes: link.notes || undefined,
    })),
    semantic_tags: api.semantic_tags,
    isContainer: !api.appears_in || api.appears_in.length === 0,
  };
}

// ── Build cross-reference indexes ──

function buildIndexes(
  domains: Domain[],
  datasets: Dataset[],
  models: Model[]
): CatalogData {
  const domainByKey = new Map(domains.map((d) => [d.key, d]));
  const datasetByKey = new Map(datasets.map((d) => [d.key, d]));
  const modelByKey = new Map(models.map((m) => [m.key, m]));

  // Group datasets by domain
  const datasetsByDomain = new Map<string, Dataset[]>();
  for (const ds of datasets) {
    const dk = ds.domainKey || "_other";
    if (!datasetsByDomain.has(dk)) datasetsByDomain.set(dk, []);
    datasetsByDomain.get(dk)!.push(ds);
  }

  // Build model ↔ dataset cross-references via pattern matching
  const modelsForDataset = new Map<string, Model[]>();
  const datasetsForModel = new Map<
    string,
    { dataset: Dataset; columnName?: string; notes?: string }[]
  >();

  for (const model of models) {
    if (!model.appears_in) continue;
    for (const link of model.appears_in) {
      for (const ds of datasets) {
        if (!ds.isContainer && patternMatches(link.moniker_pattern, ds.key)) {
          // model → dataset
          if (!modelsForDataset.has(ds.key)) modelsForDataset.set(ds.key, []);
          const mList = modelsForDataset.get(ds.key)!;
          if (!mList.find((m) => m.key === model.key)) mList.push(model);

          // dataset → model
          if (!datasetsForModel.has(model.key))
            datasetsForModel.set(model.key, []);
          const dList = datasetsForModel.get(model.key)!;
          if (!dList.find((e) => e.dataset.key === ds.key)) {
            dList.push({
              dataset: ds,
              columnName: link.column_name,
              notes: link.notes,
            });
          }
        }
      }
    }
  }

  return {
    domains,
    datasets,
    models,
    domainByKey,
    datasetByKey,
    modelByKey,
    datasetsByDomain,
    modelsForDataset,
    datasetsForModel,
  };
}

// ── Public API ──

export async function getCatalogData(): Promise<CatalogData> {
  const [domainsRes, catalogRes, modelsRes] = await Promise.all([
    fetchDomains(),
    fetchCatalogSearch("", 500),
    fetchModels(),
  ]);

  const domains = domainsRes.domains.map(mapDomain);
  const domainKeys = domains.map((d) => d.key);
  const datasets = catalogRes.results.map((r) => mapDataset(r, domainKeys));
  const models = modelsRes.models.map(mapModel);

  return buildIndexes(domains, datasets, models);
}

/** Count of leaf (non-container) datasets in a domain */
export function datasetCountForDomain(
  data: CatalogData,
  domainKey: string
): number {
  const ds = data.datasetsByDomain.get(domainKey) || [];
  return ds.filter((d) => !d.isContainer).length;
}
