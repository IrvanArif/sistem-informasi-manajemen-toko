import { config as muatEnv } from "dotenv";
import { defineConfig, devices } from "@playwright/test";

// Akun penguji dibaca dari berkas yang tidak ikut terkirim ke repositori.
muatEnv({ path: ".env.e2e" });

/** Uji ujung-ke-ujung dijalankan terhadap tampilan HASIL BANGUN yang
 *  dilayani Apache, bukan terhadap server pengembangan.
 *
 *  Alasannya menentukan: service worker hanya ada di hasil bangun. Menguji
 *  offline terhadap server pengembangan berarti menguji sesuatu yang tidak
 *  pernah dipakai toko.
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost/toko/",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
});
