import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/classify": "http://localhost:8000",
      "/inventory": "http://localhost:8000",
      "/build-plan": "http://localhost:8000",
      "/export-pdf": "http://localhost:8000",
      "/classes": "http://localhost:8000",
    },
  },
});
