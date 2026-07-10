import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    // Scoped to implemented tests; later phases add their files as they land.
    include: [
      "tests/queue.test.ts",
      "tests/budget-service.test.ts",
      "tests/branch-protection-check.test.ts",
      "tests/retry-policy.test.ts",
      "tests/runner.test.ts",
    ],
  },
});
