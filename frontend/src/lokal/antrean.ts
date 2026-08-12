import { KesalahanApi, minta } from "../api/klien";
import { db, type BarisAntrean } from "./basisdata";

/** Jeda antar percobaan, menaik lalu berhenti naik di 15 menit.
 *  Mencoba terus-menerus saat server sedang bermasalah hanya menambah
 *  beban tanpa mempercepat apa pun (bab 05 §5.5). */
export const JEDA_DETIK = [5, 15, 60, 300, 900];

export function jedaBerikutnya(percobaan: number): number {
  return JEDA_DETIK[Math.min(percobaan, JEDA_DETIK.length - 1)];
}

/** Menyimpan nota ke antrean. Ini yang dipanggil kasir, bukan pengiriman.
 *
 * Urutannya tidak boleh dibalik: tulis dulu, kirim belakangan. Kalau
 * pengiriman didahulukan, transaksi bisa lenyap saat jaringan putus tepat
 * di tengah, dan uang sudah berpindah tangan.
 */
export async function antrekan(
  uuid_klien: string,
  nomor_nota: string,
  muatan: unknown,
): Promise<void> {
  await db.antrean.put({
    uuid_klien,
    nomor_nota,
    muatan,
    status: "menunggu",
    percobaan: 0,
    kesalahan_terakhir: null,
    dibuat_pada: Date.now(),
  });
}

export async function jumlahMenunggu(): Promise<number> {
  return db.antrean.where("status").equals("menunggu").count();
}

export async function jumlahGagal(): Promise<number> {
  return db.antrean.where("status").equals("gagal").count();
}

export async function tertuaMenunggu(): Promise<number | null> {
  const semua = await db.antrean.where("status").equals("menunggu").toArray();
  if (semua.length === 0) return null;
  return Math.min(...semua.map((b) => b.dibuat_pada));
}

export interface HasilKirim {
  terkirim: number;
  gagal: number;
  tersisa: number;
}

/** Mengirim antrean satu per satu, berurutan sesuai waktu pembuatan.
 *
 * Berurutan bukan karena server menuntutnya, melainkan agar penelusuran
 * masalah tetap masuk akal dan nomor nota terbaca berurutan di laporan.
 */
export async function kirimAntrean(): Promise<HasilKirim> {
  const menunggu = await db.antrean
    .where("status")
    .equals("menunggu")
    .sortBy("dibuat_pada");

  let terkirim = 0;
  let gagal = 0;

  for (const baris of menunggu) {
    try {
      await minta("/penjualan", { metode: "POST", muatan: baris.muatan });
      // Server menjawab 200 bila UUID-nya sudah pernah masuk, dan 201 bila
      // baru. Keduanya berarti nota itu tersimpan tepat satu kali, jadi
      // antreannya boleh dibuang.
      await db.antrean.delete(baris.uuid_klien);
      terkirim += 1;
    } catch (e) {
      const kesalahan = e instanceof KesalahanApi ? e : null;

      // 4xx berarti data ditolak dan mengulang tidak akan mengubah apa
      // pun. Ditandai gagal permanen supaya manusia melihatnya, alih-alih
      // dicoba ulang selamanya tanpa ada yang tahu.
      const permanen =
        kesalahan !== null && kesalahan.status >= 400 && kesalahan.status < 500 &&
        kesalahan.status !== 401 && kesalahan.status !== 408 &&
        kesalahan.status !== 429;

      await db.antrean.update(baris.uuid_klien, {
        status: permanen ? "gagal" : "menunggu",
        percobaan: baris.percobaan + 1,
        kesalahan_terakhir: kesalahan?.pesan ?? "Tidak bisa terhubung ke server",
      });
      gagal += 1;

      // Berhenti pada kegagalan pertama yang bersifat sementara. Meneruskan
      // ke nota berikutnya hanya akan menumpuk kegagalan yang sama.
      if (!permanen) break;
    }
  }

  return { terkirim, gagal, tersisa: await jumlahMenunggu() };
}

export async function daftarGagal(): Promise<BarisAntrean[]> {
  return db.antrean.where("status").equals("gagal").toArray();
}

/** Antrean yang menua atau menumpuk berarti ada yang tidak beres.
 *  Penjualan TIDAK PERNAH dihalangi karenanya (bab 05 §5.7). */
export function perluDiperingatkan(menunggu: number, tertua: number | null): boolean {
  if (menunggu > 50) return true;
  if (tertua === null) return false;
  return Date.now() - tertua > 24 * 60 * 60 * 1000;
}
