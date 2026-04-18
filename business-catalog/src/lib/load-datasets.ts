import { fetchNodeSummaries, fetchDomains, toSlashPath } from "./api-client";

export interface BrowseDataset {
  key: string;
  display_name: string;
  description?: string;
  domainKey: string | null;
  domainDisplayName?: string;
  domainColor?: string;
  isContainer: boolean;
  classification?: string;
  maturity?: string;
  vendor?: string;
  source_binding?: { type: string };
  schema: null;
}

export interface BrowseDomain {
  key: string;
  display_name: string;
  color: string;
}

/**
 * Load datasets for the browse view. Pass a limit for a quick first batch
 * (server-side initial paint), or omit for the full catalog.
 */
export async function loadBrowseDatasets(limit?: number): Promise<{
  datasets: BrowseDataset[];
  domains: BrowseDomain[];
  total: number;
}> {
  const [summaryRes, domainsRes] = await Promise.all([
    fetchNodeSummaries(limit),
    fetchDomains(),
  ]);

  const domainByName = new Map(
    domainsRes.domains.map((d) => [d.name, d])
  );
  const domainKeys = domainsRes.domains.map((d) => d.name);

  const datasets = summaryRes.nodes.map((node) => {
    const domainKey =
      node.resolved_domain ||
      node.domain ||
      domainKeys.find(
        (dk) =>
          node.path === dk ||
          node.path.startsWith(dk + ".") ||
          node.path.startsWith(dk + "/")
      ) ||
      null;
    const domain = domainKey ? domainByName.get(domainKey) : null;
    return {
      key: toSlashPath(node.path),
      display_name: node.display_name,
      description: node.description,
      domainKey,
      domainDisplayName: domain?.display_name,
      domainColor: domain?.color,
      isContainer: !node.is_leaf,
      classification: node.classification,
      maturity: node.maturity || "bronze",
      vendor: node.vendor || undefined,
      source_binding: node.source_type ? { type: node.source_type } : undefined,
      schema: null as null,
    };
  });

  const domains = domainsRes.domains.map((d) => ({
    key: d.name,
    display_name: d.display_name,
    color: d.color,
  }));

  return { datasets, domains, total: summaryRes.total };
}
