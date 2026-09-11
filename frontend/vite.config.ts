import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(import.meta.dirname, "./src") } },
  server: {
    port: 5174,
    // API dilayani backend Rust (backend/), bukan middleware dev — jadi build
    // produksi memakai jalur yang sama dengan dev.
    proxy: { "/api": "http://localhost:8000", "/health": "http://localhost:8000" },
  },
});
