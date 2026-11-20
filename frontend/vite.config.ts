import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(import.meta.dirname, "./src") } },
  server: {
    port: 5174,
    // The Rust backend serves the API in dev too, so dev and production share one path.
    proxy: { "/api": "http://localhost:8100", "/health": "http://localhost:8100" },
  },
});
