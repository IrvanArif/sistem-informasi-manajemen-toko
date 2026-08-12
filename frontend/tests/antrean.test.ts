import "fake-indexeddb/auto";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { simpanToken } from "../src/api/klien";
import {
  antrekan,
  daftarGagal,
  jedaBerikutnya,
  jumlahGagal,
  jumlahMenunggu,
  kirimAntrean,
  perluDiperingatkan,
} from "../src/lokal/antrean";
import { db } from "../src/lokal/basisdata";

function jawab(isi: unknown, status = 200): Response {
  return new Response(status === 204 ? null : JSON.stringify(isi), { status });
}

const NOTA = { uuid_klien: "u1", nomor_nota: "20260812-K1-0001", total: 10_500 };

beforeEach(async () => {
  await db.antrean.clear();
  localStorage.clear();
  simpanToken("a", "s");
  vi.restoreAllMocks();
});

describe("antrean penjualan", () => {
  it("menyimpan nota sebelum pengiriman diusahakan", async () => {
    // Tidak ada fetch yang disiapkan. Kalau antrekan() memanggil jaringan,
    // uji ini gagal, dan itu memang yang harus dijaga: nota ditulis lebih
    // dulu supaya tidak lenyap saat jaringan putus di tengah.
    await antrekan(NOTA.uuid_klien, NOTA.nomor_nota, NOTA);
    expect(await jumlahMenunggu()).toBe(1);
  });

  it("membuang dari antrean setelah terkirim", async () => {
    await antrekan(NOTA.uuid_klien, NOTA.nomor_nota, NOTA);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jawab({ id: 1 }, 201)));

    const hasil = await kirimAntrean();

    expect(hasil.terkirim).toBe(1);
    expect(await jumlahMenunggu()).toBe(0);
  });

  it("jawaban 200 juga dianggap berhasil, karena berarti sudah tersimpan", async () => {
    await antrekan(NOTA.uuid_klien, NOTA.nomor_nota, NOTA);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jawab({ id: 1 }, 200)));

    expect((await kirimAntrean()).terkirim).toBe(1);
    expect(await jumlahMenunggu()).toBe(0);
  });

  it("tetap menunggu saat jaringan putus", async () => {
    await antrekan(NOTA.uuid_klien, NOTA.nomor_nota, NOTA);
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("network")));

    await kirimAntrean();

    expect(await jumlahMenunggu()).toBe(1);
    expect(await jumlahGagal()).toBe(0);
    expect((await db.antrean.get("u1"))?.percobaan).toBe(1);
  });

  it("tetap menunggu saat server balas 5xx", async () => {
    await antrekan(NOTA.uuid_klien, NOTA.nomor_nota, NOTA);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jawab({ pesan: "aduh" }, 503)));

    await kirimAntrean();
    expect(await jumlahMenunggu()).toBe(1);
  });

  it("ditandai gagal permanen saat data ditolak 422", async () => {
    await antrekan(NOTA.uuid_klien, NOTA.nomor_nota, NOTA);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      jawab({ kode: "TOTAL_TIDAK_COCOK", pesan: "Total nota tidak cocok" }, 422),
    ));

    await kirimAntrean();

    expect(await jumlahGagal()).toBe(1);
    expect(await jumlahMenunggu()).toBe(0);
    expect((await daftarGagal())[0].kesalahan_terakhir).toContain("tidak cocok");
  });

  it("401 tidak dianggap permanen, karena token bisa disegarkan", async () => {
    await antrekan(NOTA.uuid_klien, NOTA.nomor_nota, NOTA);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      jawab({ kode: "SESI_HABIS", pesan: "Sesi berakhir" }, 401),
    ));

    await kirimAntrean();
    expect(await jumlahMenunggu()).toBe(1);
  });

  it("berhenti pada kegagalan sementara, tidak menumpuk kegagalan sama", async () => {
    await antrekan("u1", "N1", NOTA);
    await antrekan("u2", "N2", NOTA);
    await antrekan("u3", "N3", NOTA);
    const tiruan = vi.fn().mockRejectedValue(new TypeError("network"));
    vi.stubGlobal("fetch", tiruan);

    await kirimAntrean();

    expect(tiruan).toHaveBeenCalledTimes(1);
    expect(await jumlahMenunggu()).toBe(3);
  });

  it("mengirim berurutan sesuai waktu pembuatan", async () => {
    await antrekan("u1", "N1", { urut: 1 });
    await new Promise((r) => setTimeout(r, 5));
    await antrekan("u2", "N2", { urut: 2 });

    const tiruan = vi.fn().mockResolvedValue(jawab({ id: 1 }, 201));
    vi.stubGlobal("fetch", tiruan);
    await kirimAntrean();

    const dikirim = tiruan.mock.calls.map((c) => JSON.parse(c[1].body).urut);
    expect(dikirim).toEqual([1, 2]);
  });
});

describe("jeda percobaan", () => {
  it("menaik lalu berhenti naik", () => {
    expect(jedaBerikutnya(0)).toBe(5);
    expect(jedaBerikutnya(1)).toBe(15);
    expect(jedaBerikutnya(4)).toBe(900);
    expect(jedaBerikutnya(99)).toBe(900);
  });
});

describe("peringatan antrean", () => {
  it("memperingatkan saat antrean menumpuk", () => {
    expect(perluDiperingatkan(51, Date.now())).toBe(true);
    expect(perluDiperingatkan(3, Date.now())).toBe(false);
  });

  it("memperingatkan saat antrean menua lebih dari sehari", () => {
    const kemarin = Date.now() - 25 * 60 * 60 * 1000;
    expect(perluDiperingatkan(1, kemarin)).toBe(true);
  });

  it("antrean kosong tidak memperingatkan", () => {
    expect(perluDiperingatkan(0, null)).toBe(false);
  });
});
