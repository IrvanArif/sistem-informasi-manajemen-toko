import "fake-indexeddb/auto";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ProdukTampil } from "../src/api/domain";
import { simpanToken } from "../src/api/klien";
import { db, penandaSinkron } from "../src/lokal/basisdata";
import { cariLokal, jamMelesetJauh, katalogSiap, sinkronKatalog } from "../src/lokal/replika";

function produk(ubah: Partial<ProdukTampil> = {}): ProdukTampil {
  return {
    id: 1, kode: "P001", nama: "Indomie Goreng", kategori_id: null,
    satuan_dasar: "bungkus", stok: "120.000", stok_minimum: "0.000",
    perlu_dilengkapi: false, aktif: true,
    satuan: [
      { id: 1, nama: "bungkus", faktor: "1.000", harga_jual: 3500,
        barcode: "8991002101234", is_dasar: true, aktif: true },
      { id: 2, nama: "dus", faktor: "40.000", harga_jual: 130000,
        barcode: "8991002109999", is_dasar: false, aktif: true },
    ],
    ...ubah,
  };
}

function jawabSinkron(produkList: ProdukTampil[], waktu = "2026-08-12T10:00:00Z"): Response {
  return new Response(
    JSON.stringify({ produk: produkList, kategori: [], waktu_server: waktu }),
    { status: 200 },
  );
}

beforeEach(async () => {
  await db.produk.clear();
  await db.kategori.clear();
  await db.meta.clear();
  localStorage.clear();
  simpanToken("a", "s");
  vi.restoreAllMocks();
});

describe("sinkron katalog", () => {
  it("menyimpan produk ke salinan lokal", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jawabSinkron([produk()])));
    const hasil = await sinkronKatalog();
    expect(hasil.produk).toBe(1);
    expect(await katalogSiap()).toBe(true);
  });

  it("menyimpan waktu server sebagai penanda, bukan jam perangkat", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      jawabSinkron([produk()], "2026-08-12T10:00:00Z"),
    ));
    await sinkronKatalog();
    expect(await penandaSinkron.baca()).toBe("2026-08-12T10:00:00Z");
  });

  it("mengirim penanda apa adanya pada sinkron berikutnya", async () => {
    const tiruan = vi.fn()
      .mockResolvedValueOnce(jawabSinkron([produk()], "2026-08-12T10:00:00Z"))
      .mockResolvedValueOnce(jawabSinkron([], "2026-08-12T11:00:00Z"));
    vi.stubGlobal("fetch", tiruan);

    await sinkronKatalog();
    await sinkronKatalog();

    const jalurKedua = tiruan.mock.calls[1][0] as string;
    expect(jalurKedua).toContain("sejak=2026-08-12T10:00:00Z");
    // Penanda berakhiran Z tidak butuh penyandian; kalau ia berakhir +00:00,
    // tanda + akan diuraikan sebagai spasi dan server menolak 422.
    expect(jalurKedua).not.toContain("+");
  });

  it("mencatat selisih jam perangkat terhadap server", async () => {
    const jauh = new Date(Date.now() - 60 * 60 * 1000).toISOString();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jawabSinkron([produk()], jauh)));
    await sinkronKatalog();
    expect(await jamMelesetJauh()).toBe(true);
  });

  it("jam yang tepat tidak dianggap meleset", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      jawabSinkron([produk()], new Date().toISOString()),
    ));
    await sinkronKatalog();
    expect(await jamMelesetJauh()).toBe(false);
  });

  it("produk yang dinonaktifkan ikut tersalin", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      jawabSinkron([produk({ aktif: false })]),
    ));
    await sinkronKatalog();
    expect((await db.produk.get(1))?.isi.aktif).toBe(false);
  });
});

describe("pencarian lokal", () => {
  beforeEach(async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jawabSinkron([
      produk(),
      produk({ id: 2, kode: "P002", nama: "Indomie Soto",
               satuan: [{ id: 3, nama: "bungkus", faktor: "1.000", harga_jual: 3500,
                          barcode: "8991002100000", is_dasar: true, aktif: true }] }),
    ])));
    await sinkronKatalog();
  });

  it("barcode langsung menemukan satu barang", async () => {
    const hasil = await cariLokal("8991002109999");
    expect(hasil.map((p) => p.nama)).toEqual(["Indomie Goreng"]);
  });

  it("barcode didahulukan atas nama", async () => {
    expect((await cariLokal("indomie")).length).toBe(2);
    expect((await cariLokal("8991002100000")).map((p) => p.nama)).toEqual(["Indomie Soto"]);
  });

  it("kode persis didahulukan atas nama", async () => {
    expect((await cariLokal("P002")).map((p) => p.kode)).toEqual(["P002"]);
  });

  it("nama sebagian tidak peduli huruf besar kecil", async () => {
    expect((await cariLokal("GORENG")).length).toBe(1);
  });

  it("bekerja tanpa jaringan sama sekali", async () => {
    // Jaringan dimatikan total setelah katalog tersalin. Pencarian tetap
    // harus jalan, karena inilah inti kemampuan offline.
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("network")));
    expect((await cariLokal("indomie")).length).toBe(2);
  });

  it("produk nonaktif tidak muncul", async () => {
    await db.produk.put({ id: 1, isi: produk({ aktif: false }), diubah_pada: Date.now() });
    expect((await cariLokal("Goreng")).length).toBe(0);
  });

  it("kata kosong tidak mengembalikan apa pun", async () => {
    expect(await cariLokal("")).toEqual([]);
  });
});
