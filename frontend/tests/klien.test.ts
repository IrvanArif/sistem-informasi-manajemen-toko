import { describe, expect, it, vi } from "vitest";
import {
  KesalahanApi,
  ambilTokenAkses,
  hapusToken,
  minta,
  simpanToken,
  sudahMasuk,
} from "../src/api/klien";

function jawab(isi: unknown, status = 200): Response {
  return new Response(status === 204 ? null : JSON.stringify(isi), { status });
}

describe("penyimpanan token", () => {
  it("menyimpan, membaca, dan menghapus", () => {
    expect(sudahMasuk()).toBe(false);
    simpanToken("a", "s");
    expect(ambilTokenAkses()).toBe("a");
    expect(sudahMasuk()).toBe(true);
    hapusToken();
    expect(ambilTokenAkses()).toBeNull();
  });
});

describe("permintaan", () => {
  it("menyisipkan token ke kepala permintaan", async () => {
    simpanToken("token-uji", "s");
    const tiruan = vi.fn().mockResolvedValue(jawab({ ok: true }));
    vi.stubGlobal("fetch", tiruan);

    await minta("/auth/saya");

    const kepala = tiruan.mock.calls[0][1].headers;
    expect(kepala.Authorization).toBe("Bearer token-uji");
  });

  it("tidak menyisipkan kepala saat belum masuk", async () => {
    const tiruan = vi.fn().mockResolvedValue(jawab({ ok: true }));
    vi.stubGlobal("fetch", tiruan);

    await minta("/auth/masuk", { metode: "POST", muatan: {} });

    expect(tiruan.mock.calls[0][1].headers.Authorization).toBeUndefined();
  });

  it("mengubah jawaban kesalahan menjadi KesalahanApi", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jawab({ kode: "KREDENSIAL_SALAH", pesan: "Nama pengguna atau sandi keliru" }, 401),
      ),
    );

    await expect(minta("/auth/masuk", { metode: "POST", muatan: {} })).rejects.toMatchObject({
      kode: "KREDENSIAL_SALAH",
      status: 401,
    });
  });

  it("menampilkan pesan server apa adanya", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jawab({ kode: "X", pesan: "Pesan khusus dari server" }, 422)),
    );

    await expect(minta("/apa-pun")).rejects.toThrow("Pesan khusus dari server");
  });

  it("memberi pesan yang bisa dibaca saat jawaban tidak berbentuk JSON", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("<html>502</html>", { status: 502 })),
    );

    try {
      await minta("/apa-pun");
      expect.unreachable();
    } catch (e) {
      expect((e as KesalahanApi).pesan).toContain("Coba lagi");
    }
  });

  it("mengembalikan undefined untuk 204", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jawab(null, 204)));
    await expect(minta("/auth/keluar", { metode: "POST" })).resolves.toBeUndefined();
  });
});

describe("penyegaran token otomatis", () => {
  it("menukar token lalu mengulang permintaan saat kena 401", async () => {
    simpanToken("kedaluwarsa", "segar-lama");
    const tiruan = vi
      .fn()
      .mockResolvedValueOnce(jawab({ kode: "SESI_HABIS", pesan: "Sesi berakhir" }, 401))
      .mockResolvedValueOnce(jawab({ token_akses: "baru", token_segar: "segar-baru" }))
      .mockResolvedValueOnce(jawab([{ id: 1 }]));
    vi.stubGlobal("fetch", tiruan);

    const hasil = await minta<{ id: number }[]>("/pengguna");

    expect(hasil).toEqual([{ id: 1 }]);
    expect(ambilTokenAkses()).toBe("baru");
    expect(tiruan).toHaveBeenCalledTimes(3);
  });

  it("membuang token dan menyerah bila penyegaran juga gagal", async () => {
    simpanToken("kedaluwarsa", "segar-lama");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jawab({ kode: "SESI_HABIS", pesan: "Sesi berakhir" }, 401)),
    );

    await expect(minta("/pengguna")).rejects.toMatchObject({ status: 401 });
    expect(ambilTokenAkses()).toBeNull();
  });

  it("tidak mencoba menyegarkan saat yang gagal justru endpoint auth", async () => {
    simpanToken("a", "s");
    const tiruan = vi
      .fn()
      .mockResolvedValue(jawab({ kode: "KREDENSIAL_SALAH", pesan: "keliru" }, 401));
    vi.stubGlobal("fetch", tiruan);

    await expect(minta("/auth/masuk", { metode: "POST", muatan: {} })).rejects.toBeInstanceOf(
      KesalahanApi,
    );
    expect(tiruan).toHaveBeenCalledTimes(1);
  });
});
