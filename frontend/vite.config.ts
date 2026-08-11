import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
// Diimpor dari vitest/config, bukan vite, supaya bagian `test` di bawah
// dikenali tipenya.
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { port: 5173 },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/persiapan.ts"],
    include: ["tests/**/*.test.{ts,tsx}"],
  },
});
