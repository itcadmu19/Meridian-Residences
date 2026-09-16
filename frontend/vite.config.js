import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Bind all interfaces, not just localhost - required so the Vite dev
    // server is reachable from outside a Docker container (and has no
    // effect on plain local `npm run dev`, which still works the same).
    host: true,
  },
});