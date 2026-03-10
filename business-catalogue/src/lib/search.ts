import type { CatalogData } from "./data-loader";
import type { SearchResult } from "./types";

/**
 * Simple in-memory search across domains, datasets, and models.
 */
export function search(data: CatalogData, query: string): SearchResult[] {
  const q = query.toLowerCase().trim();
  if (!q) return [];

  const results: SearchResult[] = [];
  const terms = q.split(/\s+/);

  function matches(text: string): boolean {
    const lower = text.toLowerCase();
    return terms.every((t) => lower.includes(t));
  }

  function matchScore(text: string): number {
    const lower = text.toLowerCase();
    let score = 0;
    for (const t of terms) {
      if (lower.includes(t)) score++;
      if (lower.startsWith(t)) score += 2;
      if (lower === t) score += 5;
    }
    return score;
  }

  // Search domains
  for (const domain of data.domains) {
    const searchable = `${domain.key} ${domain.display_name} ${domain.notes} ${domain.data_category}`;
    if (matches(searchable)) {
      results.push({
        type: "domain",
        key: domain.key,
        display_name: domain.display_name,
        description: domain.notes,
        url: `/categories/${domain.key}`,
      });
    }
  }

  // Search datasets
  for (const ds of data.datasets) {
    const searchable = `${ds.key} ${ds.display_name} ${ds.description || ""} ${
      ds.source_binding?.type || ""
    } ${ds.schema?.semantic_tags?.join(" ") || ""} ${ds.semantic_tags?.join(" ") || ""}`;
    if (matches(searchable)) {
      results.push({
        type: "dataset",
        key: ds.key,
        display_name: ds.display_name,
        description: ds.description,
        url: `/datasets/${ds.key}`,
      });
    }
  }

  // Search models
  for (const model of data.models) {
    const searchable = `${model.key} ${model.display_name} ${
      model.description || ""
    } ${model.formula || ""} ${model.semantic_tags?.join(" ") || ""}`;
    if (matches(searchable)) {
      results.push({
        type: "model",
        key: model.key,
        display_name: model.display_name,
        description: model.description,
        url: `/fields/${model.key}`,
      });
    }
  }

  // Sort by relevance
  results.sort((a, b) => {
    const scoreA = matchScore(
      `${a.key} ${a.display_name} ${a.description || ""}`
    );
    const scoreB = matchScore(
      `${b.key} ${b.display_name} ${b.description || ""}`
    );
    return scoreB - scoreA;
  });

  return results.slice(0, 50);
}
