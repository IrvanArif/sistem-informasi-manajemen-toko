import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { Pengguna } from "../src/api/domain";
import { LayarPengguna } from "../src/fitur/pengguna/LayarPengguna";
import { simpanToken } from "../src/api/klien";

const PEMILIK: Pengguna = {
  id: 1,
  nama_pengguna: "irvan",
  nama_lengkap: "Irvan",
  peran: "pemilik",
  aktif: true,
};

function jawab(isi: unknown, status = 200): Response {
  return new Response(status === 204 ? null : JSON.stringify(isi), { status });
}

describe("LayarPengguna", () => {
  it("menampilkan daftar pengguna", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jawab([PEMILIK])));
    render(<LayarPengguna saya={PEMILIK} />);
    expect(await screen.findByText("Irvan")).toBeInTheDocument();
  });

  it("menandai akun milik sendiri", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jawab([PEMILIK])));
    render(<LayarPengguna saya={PEMILIK} />);
    expect(await screen.findByText(/Anda/)).toBeInTheDocument();
  });

  it("menampilkan pesan server saat menonaktifkan pemilik terakhir", async () => {
    simpanToken("a", "s");
    const tiruan = vi
      .fn()
      .mockResolvedValueOnce(jawab([PEMILIK]))
      .mockResolvedValueOnce(
        jawab(
          {
            kode: "PEMILIK_TERAKHIR",
            pesan:
              "Tindakan ini menyisakan nol akun pemilik aktif. " +
              "Tunjuk pemilik lain lebih dulu.",
          },
          422,
        ),
      );
    vi.stubGlobal("fetch", tiruan);

    render(<LayarPengguna saya={PEMILIK} />);
    await userEvent.click(await screen.findByRole("button", { name: "Nonaktifkan" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("nol akun pemilik aktif");
  });

  it("form akun baru mengirim peran kasir", async () => {
    simpanToken("a", "s");
    const tiruan = vi
      .fn()
      .mockResolvedValueOnce(jawab([PEMILIK]))
      .mockResolvedValueOnce(jawab({ id: 2 }, 201))
      .mockResolvedValueOnce(jawab([PEMILIK]));
    vi.stubGlobal("fetch", tiruan);

    render(<LayarPengguna saya={PEMILIK} />);
    await userEvent.click(await screen.findByRole("button", { name: "Tambah akun" }));
    await userEvent.type(screen.getByLabelText("Nama pengguna"), "kasir1");
    await userEvent.type(screen.getByLabelText("Nama lengkap"), "Kasir Satu");
    await userEvent.type(screen.getByLabelText("Sandi"), "sandikasir1");
    await userEvent.click(screen.getByRole("button", { name: "Simpan" }));

    const muatan = JSON.parse(tiruan.mock.calls[1][1].body);
    expect(muatan.peran).toBe("kasir");
    expect(muatan.nama_pengguna).toBe("kasir1");
  });

  it("menampilkan pesan saat server tidak bisa dihubungi", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("network")));
    render(<LayarPengguna saya={PEMILIK} />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Tidak bisa terhubung");
  });
});
