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
