/** Tipe domain, diturunkan dari skema OpenAPI yang dibangkitkan Python.
 *
 * Tidak ada bentuk data yang diketik ulang di sini. Kalau bentuk data di
 * server berubah, berkas ini ikut berubah sendiri dan pemakaian yang tidak
 * menyesuaikan akan gagal dikompilasi. Itulah gunanya membangkitkan tipe
 * dari OpenAPI (ADR-0002).
 *
 * Bangkitkan ulang dengan: npm run tipe
 */
import type { components } from "./tipe";

export type Pengguna = components["schemas"]["PenggunaKeluar"];
export type Peran = components["schemas"]["Peran"];
export type JawabanToken = components["schemas"]["JawabanToken"];
export type BuatPengguna = components["schemas"]["BuatPengguna"];
export type UbahPengguna = components["schemas"]["UbahPengguna"];

export type Produk = components["schemas"]["ProdukKeluar"];
export type ProdukKasir = components["schemas"]["ProdukKeluarKasir"];
export type Satuan = components["schemas"]["SatuanKeluar"];
export type SatuanMasuk = components["schemas"]["SatuanMasuk"];
export type ProdukMasuk = components["schemas"]["ProdukMasuk"];
export type Kategori = components["schemas"]["KategoriKeluar"];
export type HasilImpor = components["schemas"]["HasilImpor"];
export type Mutasi = components["schemas"]["MutasiKeluar"];

/** Produk sebagaimana diterima peran mana pun. hpp hanya ada untuk pemilik. */
export type ProdukTampil = ProdukKasir & { hpp?: string };

/** Rupiah selalu bilangan bulat. Ditulis dengan pemisah ribuan gaya Indonesia. */
export function rupiah(n: number): string {
  return "Rp" + n.toLocaleString("id-ID");
}

/** Jumlah datang sebagai string dari server, dengan angka desimal tetap.
 *  Nol di belakang koma dibuang agar "24.000 botol" terbaca "24 botol". */
export function jumlah(teks: string): string {
  const n = Number(teks);
  if (!Number.isFinite(n)) return teks;
  return n.toLocaleString("id-ID", { maximumFractionDigits: 3 });
}
