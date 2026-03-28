import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow reading YAML files from the parent directory
  serverExternalPackages: ["js-yaml"],
  experimental: {
    fetchCacheMaxMemorySize: 10 * 1024 * 1024, // 10 MB
  },
  async rewrites() {
    return [
      {
        // Proxy community contributions API to FastAPI management service
        source: "/api/contributions/:path*",
        destination: `${process.env.COMMUNITY_API_URL || "http://localhost:8052"}/community/:path*`,
      },
    ];
  },
};

export default nextConfig;
