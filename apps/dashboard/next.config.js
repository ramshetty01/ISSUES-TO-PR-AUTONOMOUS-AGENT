/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Bundle the workspace types package rather than treating it as external.
  transpilePackages: ["@itpr/shared-types"],
};

export default nextConfig;
