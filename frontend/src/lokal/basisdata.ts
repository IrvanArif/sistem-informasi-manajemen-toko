import Dexie, { type EntityTable } from "dexie";
import type { Kategori, ProdukTampil } from "../api/domain";

/** Penjualan yang menunggu dikirim ke server.
 *
 * Nota SELALU ditulis ke sini sebelum pengiriman diusahakan. Kalau
 * pengiriman didahulukan, transaksi bisa lenyap saat jaringan putus tepat
 * di tengah, dan uang sudah berpindah tangan (bab 05 §5.5).
 */
export interface BarisAntrean {
  uuid_klien: string;
  nomor_nota: string;
  muatan: unknown;
  status: "menunggu" | "gagal";
  percobaan: number;
  kesalahan_terakhir: string | null;
  dibuat_pada: number;
}

/** Salinan katalog. Sengaja TANPA hpp: kasir tidak berhak melihat harga
 *  modal, dan data yang tidak pernah dikirim ke perangkat tidak bisa
 *  bocor dari perangkat (bab 05 §5.3). */
export interface ProdukLokal {
  id: number;
  isi: ProdukTampil;
  diubah_pada: number;
}

export interface Meta {
  kunci: string;
  nilai: string;
}

class BasisDataToko extends Dexie {
  produk!: EntityTable<ProdukLokal, "id">;
  kategori!: EntityTable<Kategori, "id">;
  antrean!: EntityTable<BarisAntrean, "uuid_klien">;
  meta!: EntityTable<Meta, "kunci">;

  constructor() {
    super("toko");
    this.version(1).stores({
      produk: "id",
      kategori: "id",
      antrean: "uuid_klien, status, dibuat_pada",
      meta: "kunci",
    });
  }
}

export const db = new BasisDataToko();

const KUNCI_SINKRON = "waktu_sinkron_terakhir";
const KUNCI_SELISIH_JAM = "selisih_jam_detik";

export async function bacaMeta(kunci: string): Promise<string | null> {
  return (await db.meta.get(kunci))?.nilai ?? null;
}

export async function tulisMeta(kunci: string, nilai: string): Promise<void> {
  await db.meta.put({ kunci, nilai });
}

export const penandaSinkron = {
  baca: () => bacaMeta(KUNCI_SINKRON),
  tulis: (nilai: string) => tulisMeta(KUNCI_SINKRON, nilai),
};

export const selisihJam = {
  baca: async () => Number((await bacaMeta(KUNCI_SELISIH_JAM)) ?? "0"),
  tulis: (detik: number) => tulisMeta(KUNCI_SELISIH_JAM, String(detik)),
};

/** Meminta browser tidak menyingkirkan data kita sendiri.
 *
 * Tanpa ini, browser boleh membuang IndexedDB saat ruang penyimpanan
 * menipis, dan penjualan yang masih menunggu kirim ikut hilang
 * (bab 05 §5.8). Peredam, bukan jaminan.
 */
export async function mintaPenyimpananPermanen(): Promise<boolean> {
  if (!navigator.storage?.persist) return false;
  if (await navigator.storage.persisted()) return true;
  return navigator.storage.persist();
}
