import type { Kategori, ProdukTampil } from "../api/domain";
import { minta } from "../api/klien";
import { db, penandaSinkron, selisihJam } from "./basisdata";

interface JawabanSinkron {
  produk: ProdukTampil[];
  kategori: Kategori[];
  waktu_server: string;
}

/** Menarik perubahan katalog sejak sinkron terakhir.
 *
 * Penandanya adalah waktu SERVER, bukan waktu perangkat. Jam komputer
 * toko bisa meleset berhari-hari, dan penanda yang salah membuat
 * perubahan katalog terlewat diam-diam (bab 05 §5.4).
 */
export async function sinkronKatalog(): Promise<{ produk: number; kategori: number }> {
  const sejak = await penandaSinkron.baca();
  const jalur = sejak ? `/sinkron/katalog?sejak=${sejak}` : "/sinkron/katalog";
  const jawaban = await minta<JawabanSinkron>(jalur);

  await db.transaction("rw", db.produk, db.kategori, db.meta, async () => {
    if (jawaban.produk.length > 0) {
      await db.produk.bulkPut(
        jawaban.produk.map((p) => ({ id: p.id, isi: p, diubah_pada: Date.now() })),
      );
    }
    if (jawaban.kategori.length > 0) {
      await db.kategori.bulkPut(jawaban.kategori);
    }
    await penandaSinkron.tulis(jawaban.waktu_server);
  });

  // Jam perangkat yang meleset merusak waktu_transaksi, dan itu merusak
  // setiap laporan yang memakainya. Selisihnya dicatat agar bisa
  // diperingatkan (bab 05 §5.5).
  const selisih = Math.round(
    (Date.now() - new Date(jawaban.waktu_server).getTime()) / 1000,
  );
  await selisihJam.tulis(selisih);

  return { produk: jawaban.produk.length, kategori: jawaban.kategori.length };
}

export async function jamMelesetJauh(): Promise<boolean> {
  return Math.abs(await selisihJam.baca()) > 300;
}

export async function katalogSiap(): Promise<boolean> {
  return (await db.produk.count()) > 0;
}

/** Pencarian dari salinan lokal: barcode, lalu kode, lalu nama.
 *
 * Inilah yang membuat pencarian seketika sekaligus tetap hidup saat
 * internet mati. Urutannya sama persis dengan di server, karena pindaian
 * barcode harus langsung menemukan satu barang tanpa pilihan.
 */
export async function cariLokal(kata: string, batas = 8): Promise<ProdukTampil[]> {
  const bersih = kata.trim().toLowerCase();
  if (!bersih) return [];

  const semua = (await db.produk.toArray()).map((b) => b.isi).filter((p) => p.aktif);

  const lewatBarcode = semua.filter((p) =>
    p.satuan.some((s) => s.barcode?.toLowerCase() === bersih),
  );
  if (lewatBarcode.length > 0) return lewatBarcode.slice(0, batas);

  const lewatKode = semua.filter((p) => p.kode.toLowerCase() === bersih);
  if (lewatKode.length > 0) return lewatKode.slice(0, batas);

  return semua
    .filter((p) => p.nama.toLowerCase().includes(bersih))
    .sort((a, b) => a.nama.localeCompare(b.nama))
    .slice(0, batas);
}
