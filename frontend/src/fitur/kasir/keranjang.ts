import type { ProdukTampil, Satuan } from "../../api/domain";

export interface BarisKeranjang {
  kunci: string;
  produk: ProdukTampil;
  satuan: Satuan;
  jumlah: number;
  diskon: number;
}

/** Rupiah selalu bilangan bulat. Pembulatan dilakukan SEKALI di tingkat
 *  baris, bukan berulang di tiap langkah, karena pembulatan berulang
 *  menggeser hasil (bab 02 §2.5). */
export function subtotalBaris(b: BarisKeranjang): number {
  return Math.round(b.satuan.harga_jual * b.jumlah) - b.diskon;
}

export function subtotalKeranjang(isi: BarisKeranjang[]): number {
  return isi.reduce((jumlah, b) => jumlah + subtotalBaris(b), 0);
}

export function totalNota(isi: BarisKeranjang[], diskonNota: number): number {
  return subtotalKeranjang(isi) - diskonNota;
}

/** Nomor nota dibuat di perangkat, bukan menunggu server.
 *  Nomor yang menunggu server berarti struk yang dicetak saat internet
 *  mati tidak punya nomor (bab 03 aturan #5). */
export function nomorNotaBaru(kodePerangkat = "K1"): string {
  const t = new Date();
  const tanggal =
    t.getFullYear().toString() +
    String(t.getMonth() + 1).padStart(2, "0") +
    String(t.getDate()).padStart(2, "0");
  const urut = String(Date.now() % 10000).padStart(4, "0");
  return `${tanggal}-${kodePerangkat}-${urut}`;
}

/** Menerima koma maupun titik sebagai pemisah desimal.
 *  Pengguna Indonesia mengetik koma, papan ketik angka mengeluarkan titik,
 *  dan memaksanya konsisten hanya akan memperlambat kasir (bab 04 §4.1). */
export function bacaJumlah(teks: string): number | null {
  const bersih = teks.trim().replace(",", ".");
  if (!bersih) return null;
  const n = Number(bersih);
  return Number.isFinite(n) && n > 0 ? n : null;
}
