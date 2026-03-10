import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow reading YAML files from the parent directory
  serverExternalPackages: ["js-yaml"],
};

export default nextConfig;
