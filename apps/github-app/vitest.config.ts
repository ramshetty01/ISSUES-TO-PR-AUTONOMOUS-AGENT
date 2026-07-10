import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    include: [
      "tests/logger.test.ts",
      "tests/server.test.ts",
      "tests/webhook-verifier.test.ts",
      "tests/github-helpers.test.ts",
      "tests/filters.test.ts",
      "tests/queue.test.ts",
      "tests/issue-labeled.handler.test.ts",
      "tests/pr-comment.handler.test.ts",
      "tests/webhook-route.test.ts",
    ],
  },
});
