import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
// Diimpor dari vitest/config, bukan vite, supaya bagian `test` di bawah
// dikenali tipenya.
import { defineConfig } from "vitest/config";

// Saat dibangun untuk Apache, aplikasi dilayani dari /toko/ dan bukan dari
// akar, sehingga seluruh rujukan asetnya harus berawalan itu. Saat
// dikembangkan, ia tetap di akar agar `npm run dev` bekerja seperti biasa.
export default defineConfig(({ command }) => ({
  base: command === "build" ? "/toko/" : "/",
  plugins: [react(), tailwindcss()],
  server: { port: 5173 },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/persiapan.ts"],
    include: ["tests/**/*.test.{ts,tsx}"],
  },
}));
