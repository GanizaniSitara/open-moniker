import { NextRequest, NextResponse } from "next/server";
import { getCatalogData } from "@/lib/data-loader";
import { search } from "@/lib/search";

export async function GET(request: NextRequest) {
  const q = request.nextUrl.searchParams.get("q") || "";
  const all = request.nextUrl.searchParams.get("all");
  const data = await getCatalogData();

  // If requesting all fields (for the fields listing page)
  if (all === "fields") {
    const containers = data.models.filter((m) => m.isContainer);
    const containerNameByKey = new Map(
      containers.map((c) => [c.key, c.display_name])
    );

    const fields = data.models
      .filter((m) => !m.isContainer)
      .map((m) => {
        // Find parent container key (everything before the last /)
        const lastSlash = m.key.lastIndexOf("/");
        const parentKey = lastSlash > 0 ? m.key.substring(0, lastSlash) : "";
        const containerName = containerNameByKey.get(parentKey) || "Other";
        const datasetCount = data.datasetsForModel.get(m.key)?.length || 0;

        return {
          key: m.key,
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

  // If requesting all datasets (for the datasets listing page)
  if (all === "datasets") {
    const datasets = data.datasets.map((ds) => {
      const domain = ds.domainKey ? data.domainByKey.get(ds.domainKey) : null;
      return {
        ...ds,
        domainDisplayName: domain?.display_name,
        domainColor: domain?.color,
      };
    });
    return NextResponse.json({
      datasets,
      domains: data.domains,
    });
  }

  // Regular search
  const results = search(data, q);
  return NextResponse.json({ results });
}
