import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// Ports come from the repository's .env, the same file docker compose reads.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, path.resolve(import.meta.dirname, ".."), "");
  const backend = `http://localhost:${env.BACKEND_PORT}`;
  return {
    plugins: [react()],
    resolve: { alias: { "@": path.resolve(import.meta.dirname, "./src") } },
    server: {
      port: Number(env.FRONTEND_PORT),
      proxy: { "/api": backend, "/health": backend },
    },
  };
});
