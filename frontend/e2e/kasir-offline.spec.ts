import { expect, test, type Page } from "@playwright/test";

const API = "http://localhost/toko/api/v1";

/** Akun penguji dibaca dari lingkungan, tidak pernah ditulis di sini.
 *
 *  Repositori ini publik. Sandi yang ditulis di berkas uji akan ikut
 *  terbaca siapa saja, dan menghapusnya belakangan tidak menolong karena
 *  riwayat git menyimpannya selamanya. Isinya diatur lewat `frontend/.env.e2e`
 *  yang tidak pernah ikut terkirim.
 */
function wajib(nama: string): string {
  const nilai = process.env[nama];
  if (!nilai) {
    throw new Error(
      `${nama} belum diatur. Salin frontend/.env.e2e.contoh menjadi ` +
        "frontend/.env.e2e lalu isi dengan akun pengembangan.",
    );
  }
  return nilai;
}

const PEMILIK = {
  nama_pengguna: wajib("E2E_PENGGUNA"),
  sandi: wajib("E2E_SANDI"),
};

async function masuk(page: Page) {
  await page.goto("./");
  await page.getByLabel("Nama pengguna").fill(PEMILIK.nama_pengguna);
  await page.getByLabel("Sandi").fill(PEMILIK.sandi);
  await page.getByRole("button", { name: "Masuk" }).click();
  await expect(page.getByRole("button", { name: "Keluar" })).toBeVisible();
}

async function pastikanSesiKas(page: Page) {
  const buka = page.getByRole("button", { name: "Mulai melayani" });
  if (await buka.isVisible().catch(() => false)) {
    await page.getByLabel("Modal awal laci").fill("100000");
    await buka.click();
  }
  await expect(page.getByLabel("Cari atau pindai barcode")).toBeVisible();
}

/** Menunggu katalog benar-benar tersalin ke IndexedDB.
 *  Tanpa ini, uji offline bisa lulus semu karena katalognya kebetulan
 *  belum pernah dibutuhkan. */
async function tungguKatalogTersalin(page: Page) {
  await expect
    .poll(
      async () =>
        page.evaluate(
          () =>
            new Promise<number>((selesai) => {
              const p = indexedDB.open("toko");
              p.onsuccess = () => {
                const db = p.result;
                const t = db.transaction("produk", "readonly");
                const hitung = t.objectStore("produk").count();
                hitung.onsuccess = () => selesai(hitung.result);
                hitung.onerror = () => selesai(0);
              };
              p.onerror = () => selesai(0);
            }),
        ),
      { timeout: 20_000 },
    )
    .toBeGreaterThan(0);
}

async function stokIndomie(page: Page): Promise<number> {
  const token = await page.evaluate(() => localStorage.getItem("toko.token_akses"));
  const jawaban = await page.request.get(`${API}/produk?cari=P001`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const isi = await jawaban.json();
  return Number(isi[0].stok);
}

async function jumlahAntrean(page: Page): Promise<number> {
  return page.evaluate(
    () =>
      new Promise<number>((selesai) => {
        const p = indexedDB.open("toko");
        p.onsuccess = () => {
          const t = p.result.transaction("antrean", "readonly");
          const hitung = t.objectStore("antrean").count();
          hitung.onsuccess = () => selesai(hitung.result);
          hitung.onerror = () => selesai(-1);
        };
        p.onerror = () => selesai(-1);
      }),
  );
}

async function jualSatuBungkus(page: Page) {
  await page.getByLabel("Cari atau pindai barcode").fill("Indomie");
  await page.getByRole("button", { name: /^bungkus/ }).first().click();
  await page.getByRole("button", { name: /BAYAR/ }).click();
  await page.getByRole("button", { name: "Uang pas" }).click();
  await page.getByRole("button", { name: /Selesai/ }).click();
  await expect(page.getByText("KEMBALIAN")).toBeVisible();
}

test.describe("kasir offline", () => {
  test("aplikasi terbuka dan katalog tersalin ke perangkat", async ({ page }) => {
    await masuk(page);
    await pastikanSesiKas(page);
    await tungguKatalogTersalin(page);
    await expect(page.getByRole("status")).toContainText("Tersinkron");
  });

  test("menjual saat internet mati, lalu antrean terkirim sendiri", async ({
    page,
    context,
  }) => {
    await masuk(page);
    await pastikanSesiKas(page);
    await tungguKatalogTersalin(page);

    const stokAwal = await stokIndomie(page);

    // Internet dimatikan total.
    await context.setOffline(true);

    // Pencarian harus tetap jalan, dari salinan lokal.
    await page.getByLabel("Cari atau pindai barcode").fill("Indomie");
    await expect(page.getByText("Indomie Goreng").first()).toBeVisible();

    await page.getByRole("button", { name: /^bungkus/ }).first().click();
    await page.getByRole("button", { name: /BAYAR/ }).click();
    await page.getByRole("button", { name: "Uang pas" }).click();
    await page.getByRole("button", { name: /Selesai/ }).click();

    // Transaksi tetap selesai, dan kembaliannya tampil.
    await expect(page.getByText("KEMBALIAN")).toBeVisible();
    await expect(page.getByRole("status")).toContainText("Offline");
    expect(await jumlahAntrean(page)).toBe(1);

    // Internet kembali. Antrean harus terkirim sendiri.
    await context.setOffline(false);
    await page.evaluate(() => window.dispatchEvent(new Event("online")));

    await expect.poll(() => jumlahAntrean(page), { timeout: 30_000 }).toBe(0);
    await expect.poll(() => stokIndomie(page), { timeout: 20_000 }).toBe(stokAwal - 1);
  });

  test("tiga transaksi offline terkirim semua tanpa duplikat", async ({
    page,
    context,
  }) => {
    await masuk(page);
    await pastikanSesiKas(page);
    await tungguKatalogTersalin(page);

    const stokAwal = await stokIndomie(page);
    await context.setOffline(true);

    for (let i = 0; i < 3; i += 1) {
      await jualSatuBungkus(page);
      await page.getByRole("button", { name: /Transaksi baru/ }).click();
    }
    expect(await jumlahAntrean(page)).toBe(3);

    await context.setOffline(false);
    await page.evaluate(() => window.dispatchEvent(new Event("online")));

    await expect.poll(() => jumlahAntrean(page), { timeout: 40_000 }).toBe(0);
    // Tepat tiga, bukan enam. Kalau idempotensi rusak, angka ini yang
    // pertama memperlihatkannya.
    await expect.poll(() => stokIndomie(page), { timeout: 20_000 }).toBe(stokAwal - 3);
  });

  test("aplikasi tetap terbuka setelah dimuat ulang tanpa internet", async ({
    page,
    context,
  }) => {
    await masuk(page);
    await pastikanSesiKas(page);
    await tungguKatalogTersalin(page);

    // Service worker perlu sempat mengambil alih sebelum diuji.
    await page.waitForTimeout(2000);
    await context.setOffline(true);
    await page.reload();

    // Tanpa service worker, halaman ini gagal dimuat sama sekali, dan
    // seluruh lapisan antrean menjadi tidak berguna.
    await expect(page.getByLabel("Cari atau pindai barcode")).toBeVisible({
      timeout: 20_000,
    });
    await expect(page.getByRole("status")).toContainText("Offline");
  });
});
