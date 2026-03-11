/**
 * Vendor directory — loaded from vendors.yaml at repo root.
 * 
 * Server components: import { getVendors } from "@/lib/vendors"
 * Client components: fetch from /api/vendors
 */
import fs from "fs";
import path from "path";
import yaml from "js-yaml";

export interface Vendor {
  key: string;
  name: string;
  description: string;
  category: string;
  datasetCount: number;
  website?: string;
}

let _cache: Vendor[] | null = null;

export function getVendors(): Vendor[] {
  if (!_cache) {
    const repoRoot = path.resolve(process.cwd(), "..");
    const primary = path.join(repoRoot, "vendors.yaml");
    const sample = path.join(repoRoot, "sample_vendors.yaml");
    const filePath = fs.existsSync(primary) ? primary : sample;
    const raw = yaml.load(fs.readFileSync(filePath, "utf-8")) as Record<
      string,
      { name: string; description: string; category: string; website?: string }
    >;
    _cache = Object.entries(raw).map(([key, v]) => ({
      key,
      name: v.name,
      description: v.description,
      category: v.category,
      datasetCount: 0,
      website: v.website,
    }));
  }
  return _cache;
}

