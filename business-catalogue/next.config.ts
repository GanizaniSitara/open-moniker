import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow reading YAML files from the parent directory
  serverExternalPackages: ["js-yaml"],
  experimental: {
    fetchCacheMaxMemorySize: 10 * 1024 * 1024, // 10 MB
  },
};

export default nextConfig;
