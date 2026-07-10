/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Bundle the workspace types package rather than treating it as external.
  transpilePackages: ["@itpr/shared-types"],
  // Resolve TS-style ".js" import specifiers to their ".ts"/".tsx" sources so
  // webpack matches tsc's (Bundler) and vitest's resolution.
  webpack: (config) => {
    config.resolve.extensionAlias = {
      ".js": [".ts", ".tsx", ".js"],
      ".jsx": [".tsx", ".jsx"],
    };
    return config;
  },
};

export default nextConfig;
