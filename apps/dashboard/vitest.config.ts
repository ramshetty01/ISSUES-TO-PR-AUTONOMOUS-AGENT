import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["tests/setup.ts"],
    // Scoped to implemented tests; later phases add their files as they land.
    include: [
      "tests/format.test.ts",
      "tests/api.test.ts",
    ],
  },
});
