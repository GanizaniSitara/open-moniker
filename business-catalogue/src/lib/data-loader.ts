import fs from "fs";
import path from "path";
import yaml from "js-yaml";
import {
  Domain,
  Dataset,
  Model,
  MonikerLink,
  Schema,
  Ownership,
  Documentation,
  AccessPolicy,
  SourceBinding,
  ModelOwnership,
} from "./types";
import { catalogKeyToDomain, patternMatches } from "./domain-mapping";

// Repo root is one level up from business-catalogue/
const REPO_ROOT = path.resolve(process.cwd(), "..");

function loadYaml(filename: string): Record<string, unknown> {
  const filePath = path.join(REPO_ROOT, filename);
  const content = fs.readFileSync(filePath, "utf-8");
  return yaml.load(content) as Record<string, unknown>;
}

// Singleton cache
let _data: CatalogData | null = null;

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

function parseDomains(raw: Record<string, unknown>): Domain[] {
  return Object.entries(raw).map(([key, val]) => {
    const v = val as Record<string, unknown>;
    return {
      key,
      id: v.id as number,
      display_name: (v.display_name as string) || key,
      short_code: (v.short_code as string) || "",
      data_category: (v.data_category as string) || "",
      color: (v.color as string) || "#666",
      owner: (v.owner as string) || "",
      tech_custodian: (v.tech_custodian as string) || "",
      business_steward: (v.business_steward as string) || "",
      confidentiality: (v.confidentiality as string) || "internal",
      pii: (v.pii as boolean) || false,
      help_channel: (v.help_channel as string) || "",
      wiki_link: (v.wiki_link as string) || "",
      notes: (v.notes as string) || "",
    };
  });
}

function parseDatasets(
  raw: Record<string, unknown>,
  domainKeys: string[]
): Dataset[] {
  return Object.entries(raw).map(([key, val]) => {
    const v = val as Record<string, unknown>;
    const ownership = v.ownership as Ownership | undefined;
    const documentation = v.documentation as Documentation | undefined;
    const sourceBinding = v.source_binding as SourceBinding | undefined;
    const schema = v.schema as Schema | undefined;
    const accessPolicy = v.access_policy as AccessPolicy | undefined;

    return {
      key,
      display_name: (v.display_name as string) || key,
      description: v.description as string | undefined,
      ownership,
      documentation,
      source_binding: sourceBinding,
      schema,
      classification: v.classification as string | undefined,
      access_policy: accessPolicy,
      semantic_tags: v.semantic_tags as string[] | undefined,
      vendor: v.vendor as string | undefined,
      domainKey: catalogKeyToDomain(key, domainKeys) || undefined,
      isContainer: !sourceBinding,
    };
  });
}

function parseModels(raw: Record<string, unknown>): Model[] {
  return Object.entries(raw).map(([key, val]) => {
    const v = val as Record<string, unknown>;
    const appearsIn = v.appears_in as MonikerLink[] | undefined;
    const ownership = v.ownership as ModelOwnership | undefined;

    return {
      key,
      display_name: (v.display_name as string) || key,
      description: v.description as string | undefined,
      formula: v.formula as string | undefined,
      unit: v.unit as string | undefined,
      data_type: v.data_type as string | undefined,
      documentation_url: v.documentation_url as string | undefined,
      methodology_url: v.methodology_url as string | undefined,
      wiki_link: v.wiki_link as string | undefined,
      ownership,
      appears_in: appearsIn,
      semantic_tags: v.semantic_tags as string[] | undefined,
      isContainer: !appearsIn || appearsIn.length === 0,
    };
  });
}

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
    if (!datasetsByDomain.has(dk)) {
      datasetsByDomain.set(dk, []);
    }
    datasetsByDomain.get(dk)!.push(ds);
  }

  // Build model-to-dataset and dataset-to-model reverse indexes
  const modelsForDataset = new Map<string, Model[]>();
  const datasetsForModel = new Map<
    string,
    { dataset: Dataset; columnName?: string; notes?: string }[]
  >();

  for (const model of models) {
    if (!model.appears_in) continue;
    for (const link of model.appears_in) {
      // Check each dataset key against the pattern
      for (const ds of datasets) {
        if (!ds.isContainer && patternMatches(link.moniker_pattern, ds.key)) {
          // Add model to dataset's list
          if (!modelsForDataset.has(ds.key)) {
            modelsForDataset.set(ds.key, []);
          }
          const existing = modelsForDataset.get(ds.key)!;
          if (!existing.find((m) => m.key === model.key)) {
            existing.push(model);
          }

          // Add dataset to model's list
          if (!datasetsForModel.has(model.key)) {
            datasetsForModel.set(model.key, []);
          }
          const existingDs = datasetsForModel.get(model.key)!;
          if (!existingDs.find((e) => e.dataset.key === ds.key)) {
            existingDs.push({
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

export function getCatalogData(): CatalogData {
  if (_data) return _data;

  const rawDomains = loadYaml("domains.yaml");
  const rawCatalog = loadYaml("catalog.yaml");

  let rawModels: Record<string, unknown> = {};
  try {
    rawModels = loadYaml("models.yaml");
  } catch {
    // models.yaml may not exist; fall back to sample
    try {
      rawModels = loadYaml("sample_models.yaml");
    } catch {
      // No models available
    }
  }

  const domains = parseDomains(rawDomains);
  const domainKeys = domains.map((d) => d.key);
  const datasets = parseDatasets(rawCatalog, domainKeys);
  const models = parseModels(rawModels);

  _data = buildIndexes(domains, datasets, models);
  return _data;
}

/** Count of leaf (non-container) datasets in a domain */
export function datasetCountForDomain(
  data: CatalogData,
  domainKey: string
): number {
  const ds = data.datasetsByDomain.get(domainKey) || [];
  return ds.filter((d) => !d.isContainer).length;
}
