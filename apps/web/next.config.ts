import type { NextConfig } from "next";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const appDir = dirname(fileURLToPath(import.meta.url));
const workspaceRoot = join(appDir, "../..");

const nextConfig: NextConfig = {
  turbopack: {
    root: workspaceRoot
  },
  transpilePackages: ["@schluesselkinder/brand", "@schluesselkinder/ui"]
};

export default nextConfig;
