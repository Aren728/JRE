import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_ENABLE_EXPERIMENTAL_VARGAS: process.env.NEXT_PUBLIC_ENABLE_EXPERIMENTAL_VARGAS ?? 'false',
    NEXT_PUBLIC_ENABLE_ADVANCED_YOGA: process.env.NEXT_PUBLIC_ENABLE_ADVANCED_YOGA ?? 'false',
  },
};

export default nextConfig;

// NOTE: Local staging and CI both expect this app to build from the standalone
// output preset with the frontend environment variables available at build time.
// See `docker-compose.staging.yml` for the local staging environment and
// `.github/workflows/ci.yml` for the CI build matrix.
