import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { LayarMasuk } from "../src/fitur/masuk/LayarMasuk";

function jawab(isi: unknown, status = 200): Response {
  return new Response(JSON.stringify(isi), { status });
}

async function isiLalu(kirim: boolean, nama = "irvan", sandi = "rahasia123") {
  await userEvent.type(screen.getByLabelText("Nama pengguna"), nama);
  await userEvent.type(screen.getByLabelText("Sandi"), sandi);
  if (kirim) await userEvent.click(screen.getByRole("button", { name: "Masuk" }));
}

describe("LayarMasuk", () => {
  it("menyimpan token dan memanggil onBerhasil saat masuk berhasil", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jawab({ token_akses: "a", token_segar: "s" })),
    );
    const onBerhasil = vi.fn();
    render(<LayarMasuk onBerhasil={onBerhasil} />);

    await isiLalu(true);

    expect(onBerhasil).toHaveBeenCalled();
    expect(localStorage.getItem("toko.token_akses")).toBe("a");
  });

  it("menampilkan pesan dari server saat kredensial salah", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jawab({ kode: "KREDENSIAL_SALAH", pesan: "Nama pengguna atau sandi keliru" }, 401),
      ),
    );
    render(<LayarMasuk onBerhasil={vi.fn()} />);

    await isiLalu(true, "irvan", "salah");

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Nama pengguna atau sandi keliru",
    );
    expect(localStorage.getItem("toko.token_akses")).toBeNull();
  });

  it("memberi pesan yang jelas saat server tidak bisa dihubungi", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("network")));
    render(<LayarMasuk onBerhasil={vi.fn()} />);

    await isiLalu(true);

    expect(await screen.findByRole("alert")).toHaveTextContent("Tidak bisa terhubung");
  });

  it("sandi tidak pernah terlihat di layar", async () => {
    render(<LayarMasuk onBerhasil={vi.fn()} />);
    await isiLalu(false);
    expect(screen.getByLabelText("Sandi")).toHaveAttribute("type", "password");
  });

  it("kolom pertama langsung terfokus", () => {
    render(<LayarMasuk onBerhasil={vi.fn()} />);
    expect(screen.getByLabelText("Nama pengguna")).toHaveFocus();
  });

  it("tombol terkunci selama pengiriman agar tidak terkirim dua kali", async () => {
    let tuntaskan: (r: Response) => void = () => {};
    vi.stubGlobal(
      "fetch",
      vi.fn().mockReturnValue(new Promise<Response>((r) => (tuntaskan = r))),
    );
    render(<LayarMasuk onBerhasil={vi.fn()} />);

    await isiLalu(true);

    expect(screen.getByRole("button", { name: "Memproses..." })).toBeDisabled();
    tuntaskan(jawab({ token_akses: "a", token_segar: "s" }));
  });
});
