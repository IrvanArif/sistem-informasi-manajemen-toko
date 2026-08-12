import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { ProdukTampil } from "../src/api/domain";
import { LayarProduk } from "../src/fitur/produk/LayarProduk";
import { simpanToken } from "../src/api/klien";

function produk(ubah: Partial<ProdukTampil> = {}): ProdukTampil {
  return {
    id: 1,
    kode: "P001",
    nama: "Indomie Goreng",
    kategori_id: null,
    satuan_dasar: "bungkus",
    stok: "120.000",
    stok_minimum: "20.000",
    perlu_dilengkapi: false,
    aktif: true,
    satuan: [
      { id: 1, nama: "bungkus", faktor: "1.000", harga_jual: 3500,
        barcode: "899", is_dasar: true, aktif: true },
      { id: 2, nama: "dus", faktor: "40.000", harga_jual: 130000,
        barcode: null, is_dasar: false, aktif: true },
    ],
    ...ubah,
  };
}

function jawab(isi: unknown, status = 200): Response {
  return new Response(JSON.stringify(isi), { status });
}

describe("LayarProduk", () => {
  it("menampilkan produk berikut kedua satuannya", async () => {
    simpanToken("a", "s");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jawab([produk()])));

    render(<LayarProduk bolehUbah onTambah={vi.fn()} onImpor={vi.fn()} />);

    expect(await screen.findByText("Indomie Goreng")).toBeInTheDocument();
    expect(screen.getByText("120 bungkus")).toBeInTheDocument();
    expect(screen.getByText("Rp3.500")).toBeInTheDocument();
    expect(screen.getByText("Rp130.000")).toBeInTheDocument();
  });

  it("harga dus ditampilkan apa adanya, bukan kelipatan harga bungkus", async () => {
    simpanToken("a", "s");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jawab([produk()])));

    render(<LayarProduk bolehUbah onTambah={vi.fn()} onImpor={vi.fn()} />);

    await screen.findByText("Indomie Goreng");
    expect(screen.getByText("Rp130.000")).toBeInTheDocument();
    expect(screen.queryByText("Rp140.000")).not.toBeInTheDocument();
  });

  it("menandai stok minus", async () => {
    simpanToken("a", "s");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jawab([produk({ stok: "-3.000" })])));

    render(<LayarProduk bolehUbah onTambah={vi.fn()} onImpor={vi.fn()} />);
    expect(await screen.findByText("stok minus")).toBeInTheDocument();
  });

  it("menandai stok menipis", async () => {
    simpanToken("a", "s");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jawab([produk({ stok: "5.000" })])));

    render(<LayarProduk bolehUbah onTambah={vi.fn()} onImpor={vi.fn()} />);
    expect(await screen.findByText("menipis")).toBeInTheDocument();
  });

  it("membuang nol di belakang koma pada jumlah", async () => {
    simpanToken("a", "s");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jawab([produk({ stok: "24.000" })])));

    render(<LayarProduk bolehUbah onTambah={vi.fn()} onImpor={vi.fn()} />);
    expect(await screen.findByText("24 bungkus")).toBeInTheDocument();
  });

  it("menampilkan jumlah berdesimal untuk barang curah", async () => {
    simpanToken("a", "s");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      jawab([produk({ stok: "42.500", satuan_dasar: "kg" })]),
    ));

    render(<LayarProduk bolehUbah onTambah={vi.fn()} onImpor={vi.fn()} />);
    expect(await screen.findByText("42,5 kg")).toBeInTheDocument();
  });

  it("kasir tidak melihat tombol yang mengubah katalog", async () => {
    simpanToken("a", "s");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jawab([produk()])));

    render(<LayarProduk bolehUbah={false} onTambah={vi.fn()} onImpor={vi.fn()} />);

    await screen.findByText("Indomie Goreng");
    expect(screen.queryByRole("button", { name: "Tambah produk" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Impor CSV" })).not.toBeInTheDocument();
  });

  it("menunda pencarian sampai ketikan berhenti", async () => {
    simpanToken("a", "s");
    const tiruan = vi.fn().mockResolvedValue(jawab([]));
    vi.stubGlobal("fetch", tiruan);

    render(<LayarProduk bolehUbah onTambah={vi.fn()} onImpor={vi.fn()} />);
    await screen.findByText(/Belum ada produk/);

    const awal = tiruan.mock.calls.length;
    await userEvent.type(screen.getByLabelText(/Cari nama/), "indomie");

    // Tujuh huruf tidak boleh menjadi tujuh permintaan.
    expect(tiruan.mock.calls.length - awal).toBeLessThan(7);
  });

  it("menampilkan pesan saat server tidak bisa dihubungi", async () => {
    simpanToken("a", "s");
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("network")));

    render(<LayarProduk bolehUbah onTambah={vi.fn()} onImpor={vi.fn()} />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Tidak bisa terhubung");
  });
});
