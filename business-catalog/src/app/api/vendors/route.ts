import { NextResponse } from "next/server";
import { getVendors } from "@/lib/vendors";
import { fetchNodeSummaries } from "@/lib/api-client";

export async function GET() {
  const vendors = getVendors();

  // Compute dataset counts from the monolith catalog
  try {
    const nodes = await fetchNodeSummaries();
    const counts = new Map<string, number>();
    for (const node of nodes) {
      if (node.vendor) {
        counts.set(node.vendor, (counts.get(node.vendor) || 0) + 1);
      }
    }
    for (const v of vendors) {
      v.datasetCount = counts.get(v.key) || 0;
    }
  } catch {
    // Monolith unavailable — counts stay at 0
  }

  return NextResponse.json({ vendors });
}
