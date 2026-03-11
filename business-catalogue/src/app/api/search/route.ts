import { NextRequest, NextResponse } from "next/server";
import {
  fetchDomains,
  fetchNodes,
  fetchModels,
  fetchCatalogSearch,
  toSlashPath,
} from "@/lib/api-client";

export async function GET(request: NextRequest) {
  const q = request.nextUrl.searchParams.get("q") || "";
  const all = request.nextUrl.searchParams.get("all");

  try {
    // All fields (for the fields listing page)
    if (all === "fields") {
      const { models } = await fetchModels();

      // Containers have no appears_in links
      const containers = models.filter((m) => m.appears_in.length === 0);
      const containerNameByPath = new Map(
        containers.map((c) => [c.path, c.display_name])
      );

      const fields = models
        .filter((m) => m.appears_in.length > 0)
        .map((m) => {
          const lastSlash = m.path.lastIndexOf("/");
          const parentPath = lastSlash > 0 ? m.path.substring(0, lastSlash) : "";
          const containerName = containerNameByPath.get(parentPath) || "Other";

          // Count datasets this model appears in
          const datasetCount = new Set(
            m.appears_in.map((a) => a.moniker_pattern)
          ).size;

          return {
            key: m.path,
            display_name: m.display_name,
            description: m.description,
            formula: m.formula,
            unit: m.unit,
            semantic_tags: m.semantic_tags,
            containerName,
            datasetCount,
          };
        });

      return NextResponse.json({ fields });
    }

    // All datasets (for the datasets listing page)
    if (all === "datasets") {
      const [nodesRes, domainsRes] = await Promise.all([
        fetchNodes(),
        fetchDomains(),
      ]);

      const domainByName = new Map(
        domainsRes.domains.map((d) => [d.name, d])
      );
      const domainKeys = domainsRes.domains.map((d) => d.name);

      const datasets = nodesRes.nodes.map((node) => {
        // Domain is either set on the node or inferred by prefix matching
        const domainKey =
          node.resolved_domain || node.domain || domainKeys.find((dk) => node.path === dk || node.path.startsWith(dk + ".") || node.path.startsWith(dk + "/")) || null;
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
          vendor: node.vendor || undefined,
          source_binding: node.source_binding
            ? { type: node.source_binding.type }
            : undefined,
          schema: null as null, // Schema not in list view
        };
      });

      const domains = domainsRes.domains.map((d) => ({
        key: d.name,
        display_name: d.display_name,
        color: d.color,
      }));

      return NextResponse.json({ datasets, domains });
    }

    // Regular search — proxy to moniker service
    if (q) {
      const searchRes = await fetchCatalogSearch(q);
      const results = searchRes.results.map((r) => ({
        type: "dataset" as const,
        key: toSlashPath(r.path),
        display_name: r.display_name,
        description: r.description,
        url: `/datasets/${toSlashPath(r.path)}`,
      }));
      return NextResponse.json({ results });
    }

    return NextResponse.json({ results: [] });
  } catch (err) {
    const message = err instanceof Error ? err.message : "API error";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
