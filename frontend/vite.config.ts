import { readFileSync } from "node:fs";
import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// The version shown in the app comes from package.json, its one source.
const { version } = JSON.parse(
  readFileSync(path.resolve(__dirname, "package.json"), "utf-8"),
) as { version: string };

// The frontend calls the API at the relative path /api/v1 by default, so the
// dev server forwards /api to the backend. Override the target with
// RIP_BACKEND_URL, or bypass the proxy entirely with VITE_API_BASE_URL in
// frontend/.env.local (see frontend/.env.example).
const backendUrl = process.env.RIP_BACKEND_URL ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  define: {
    __APP_VERSION__: JSON.stringify(version),
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      "/api": {
        target: backendUrl,
        changeOrigin: true,
      },
    },
  },
  test: {
    // Tests assert the default relative API path; a developer's
    // frontend/.env.local must not change what they see.
    env: {
      VITE_API_BASE_URL: "/api/v1",
    },
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.ts",
  },
});
