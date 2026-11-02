import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/auth": "http://localhost:8000",
      "/lists": "http://localhost:8000",
      "/inventory": "http://localhost:8000",
      "/products": "http://localhost:8000",
      "/scanner": "http://localhost:8000",
    },
  },
});
