import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
// Diimpor dari vitest/config, bukan vite, supaya bagian `test` di bawah
// dikenali tipenya.
import { VitePWA } from "vite-plugin-pwa";
import { defineConfig } from "vitest/config";

// Saat dibangun untuk Apache, aplikasi dilayani dari /toko/ dan bukan dari
// akar, sehingga seluruh rujukan asetnya harus berawalan itu. Saat
// dikembangkan, ia tetap di akar agar `npm run dev` bekerja seperti biasa.
export default defineConfig(({ command }) => ({
  base: command === "build" ? "/toko/" : "/",
  plugins: [
    react(),
    tailwindcss(),
    // Service worker menyimpan kerangka aplikasi, sehingga layar kasir
    // tetap bisa dibuka saat internet mati. Tanpa ini, seluruh lapisan
    // antrean tidak ada gunanya: aplikasinya sendiri gagal dimuat
    // (bab 05 §5.8).
    VitePWA({
      registerType: "autoUpdate",
      manifest: {
        name: "Sistem Informasi Manajemen Toko",
        short_name: "Toko",
        lang: "id",
        start_url: command === "build" ? "/toko/" : "/",
        scope: command === "build" ? "/toko/" : "/",
        display: "standalone",
        background_color: "#ffffff",
        theme_color: "#111827",
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,svg}"],
        // Permintaan API TIDAK disimpan. Katalog sudah punya salinannya
        // sendiri di IndexedDB, dan menyimpan jawaban API akan membuat
        // kasir melihat stok basi tanpa tahu bahwa itu basi.
        navigateFallbackDenylist: [/^\/toko\/api\//, /^\/api\//],
      },
    }),
  ],
  server: { port: 5173 },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/persiapan.ts"],
    include: ["tests/**/*.test.{ts,tsx}"],
  },
}));
