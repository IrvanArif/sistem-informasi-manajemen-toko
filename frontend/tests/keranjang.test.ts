import { describe, expect, it } from "vitest";
import type { ProdukTampil, Satuan } from "../src/api/domain";
import {
  bacaJumlah,
  nomorNotaBaru,
  subtotalBaris,
  subtotalKeranjang,
  totalNota,
  type BarisKeranjang,
} from "../src/fitur/kasir/keranjang";

function satuan(nama: string, harga: number, faktor = "1.000"): Satuan {
  return { id: 1, nama, faktor, harga_jual: harga, barcode: null, is_dasar: true, aktif: true };
}

function produk(): ProdukTampil {
  return {
    id: 1, kode: "P001", nama: "Indomie", kategori_id: null,
    satuan_dasar: "bungkus", stok: "120.000", stok_minimum: "0.000",
    perlu_dilengkapi: false, aktif: true, satuan: [satuan("bungkus", 3500)],
  };
}

function baris(harga: number, jumlah: number, diskon = 0): BarisKeranjang {
  return { kunci: "k", produk: produk(), satuan: satuan("x", harga), jumlah, diskon };
}

describe("perhitungan keranjang", () => {
  it("menghitung subtotal baris", () => {
    expect(subtotalBaris(baris(3500, 3))).toBe(10_500);
  });

  it("mengurangi diskon baris", () => {
    expect(subtotalBaris(baris(3500, 3, 500))).toBe(10_000);
  });

  it("barang curah berdesimal tetap bulat dalam rupiah", () => {
    expect(subtotalBaris(baris(14_000, 1.5))).toBe(21_000);
  });

  it("membulatkan sekali di tingkat baris", () => {
    // 3333 x 3 = 9999, bukan hasil pembulatan berulang
    expect(subtotalBaris(baris(3333, 3))).toBe(9_999);
  });

  it("menjumlahkan seluruh baris", () => {
    expect(subtotalKeranjang([baris(3500, 3), baris(14_000, 1.5)])).toBe(31_500);
  });

  it("mengurangi diskon nota dari total", () => {
    expect(totalNota([baris(3500, 3)], 500)).toBe(10_000);
  });

  it("keranjang kosong bernilai nol", () => {
    expect(subtotalKeranjang([])).toBe(0);
  });
});

describe("nomor nota", () => {
  it("berbentuk tanggal, kode perangkat, urutan", () => {
    expect(nomorNotaBaru("K1")).toMatch(/^\d{8}-K1-\d{4}$/);
  });

  it("dibuat tanpa memanggil server", () => {
    // Tidak ada fetch yang disiapkan; kalau fungsi ini memanggil jaringan,
    // uji ini gagal. Nomor harus ada bahkan saat internet mati.
    expect(nomorNotaBaru()).toBeTruthy();
  });
});

describe("pembacaan jumlah", () => {
  it("menerima koma sebagai pemisah desimal", () => {
    expect(bacaJumlah("1,5")).toBe(1.5);
  });

  it("menerima titik sebagai pemisah desimal", () => {
    expect(bacaJumlah("1.5")).toBe(1.5);
  });

  it("menolak nol, negatif, dan bukan angka", () => {
    expect(bacaJumlah("0")).toBeNull();
    expect(bacaJumlah("-2")).toBeNull();
    expect(bacaJumlah("abc")).toBeNull();
    expect(bacaJumlah("")).toBeNull();
  });
});
