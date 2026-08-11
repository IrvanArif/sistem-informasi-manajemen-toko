import { useState, type FormEvent } from "react";
import type { JawabanToken } from "../../api/domain";
import { KesalahanApi, minta, simpanToken } from "../../api/klien";
import { Kolom, PesanKesalahan, Tombol } from "../../komponen/dasar";

export function LayarMasuk({ onBerhasil }: { onBerhasil: () => void }) {
  const [namaPengguna, setNamaPengguna] = useState("");
  const [sandi, setSandi] = useState("");
  const [kesalahan, setKesalahan] = useState<string | null>(null);
  const [sedangKirim, setSedangKirim] = useState(false);

  async function kirim(e: FormEvent) {
    e.preventDefault();
    setKesalahan(null);
    setSedangKirim(true);
    try {
      const jawaban = await minta<JawabanToken>("/auth/masuk", {
        metode: "POST",
        muatan: { nama_pengguna: namaPengguna, sandi },
      });
      simpanToken(jawaban.token_akses, jawaban.token_segar);
      onBerhasil();
    } catch (e) {
      setKesalahan(
        e instanceof KesalahanApi ? e.pesan : "Tidak bisa terhubung ke server",
      );
    } finally {
      setSedangKirim(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-4">
      <form onSubmit={kirim} className="w-full max-w-sm space-y-4">
        <h1 className="text-2xl font-bold text-gray-900">Masuk</h1>

        <Kolom
          label="Nama pengguna"
          autoFocus
          autoComplete="username"
          value={namaPengguna}
          onChange={(e) => setNamaPengguna(e.target.value)}
        />
        <Kolom
          label="Sandi"
          type="password"
          autoComplete="current-password"
          value={sandi}
          onChange={(e) => setSandi(e.target.value)}
        />

        <PesanKesalahan>{kesalahan}</PesanKesalahan>

        <Tombol utama type="submit" disabled={sedangKirim} className="w-full">
          {sedangKirim ? "Memproses..." : "Masuk"}
        </Tombol>
      </form>
    </main>
  );
}
