import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    // Scoped to implemented tests; later phases add their files as they land.
    include: ["tests/server.test.ts", "tests/webhook-verifier.test.ts"],
  },
});
