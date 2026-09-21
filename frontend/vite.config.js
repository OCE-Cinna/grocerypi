import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // All /auth, /lists API calls are proxied to FastAPI
      "/auth": "http://localhost:8000",
      "/lists": "http://localhost:8000",
    },
  },
});
