import { useCallback, useEffect, useState, type FormEvent } from "react";
import type { Pengguna } from "../../api/domain";
import { KesalahanApi, minta } from "../../api/klien";
import { Kolom, PesanKesalahan, Tombol } from "../../komponen/dasar";

function pesanDari(e: unknown): string {
  return e instanceof KesalahanApi ? e.pesan : "Tidak bisa terhubung ke server";
}

export function LayarPengguna({ saya }: { saya: Pengguna | null }) {
  const [daftar, setDaftar] = useState<Pengguna[]>([]);
  const [kesalahan, setKesalahan] = useState<string | null>(null);
  const [memuat, setMemuat] = useState(true);
  const [formTampil, setFormTampil] = useState(false);

  const muat = useCallback(async () => {
    try {
      setDaftar(await minta<Pengguna[]>("/pengguna"));
      setKesalahan(null);
    } catch (e) {
      setKesalahan(pesanDari(e));
    } finally {
      setMemuat(false);
    }
  }, []);

  useEffect(() => {
    void muat();
  }, [muat]);

  async function ubahAktif(p: Pengguna) {
    setKesalahan(null);
    try {
      await minta(`/pengguna/${p.id}`, { metode: "PATCH", muatan: { aktif: !p.aktif } });
      await muat();
    } catch (e) {
      setKesalahan(pesanDari(e));
    }
  }

  return (
    <section className="p-4 max-w-2xl mx-auto space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-gray-900">Pengguna</h1>
        <Tombol onClick={() => setFormTampil((v) => !v)}>
          {formTampil ? "Tutup" : "Tambah akun"}
        </Tombol>
      </div>

      <PesanKesalahan>{kesalahan}</PesanKesalahan>

      {formTampil && (
        <FormAkunBaru
          onSelesai={() => {
            setFormTampil(false);
            void muat();
          }}
          onGagal={setKesalahan}
        />
      )}

      {memuat ? (
        <p className="text-gray-700">Memuat...</p>
      ) : (
        <ul className="space-y-2">
          {daftar.map((p) => (
            <li
              key={p.id}
              className="flex flex-wrap items-center justify-between gap-3
                         rounded border border-gray-300 p-3"
            >
              <div>
                <p className="font-medium text-gray-900">{p.nama_lengkap}</p>
                <p className="text-sm text-gray-700">
                  {p.nama_pengguna} &middot; {p.peran}
                  {!p.aktif && " · nonaktif"}
                  {saya?.id === p.id && " · Anda"}
                </p>
              </div>
              <Tombol onClick={() => void ubahAktif(p)}>
                {p.aktif ? "Nonaktifkan" : "Aktifkan"}
              </Tombol>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function FormAkunBaru({
  onSelesai,
  onGagal,
}: {
  onSelesai: () => void;
  onGagal: (pesan: string) => void;
}) {
  const [namaPengguna, setNamaPengguna] = useState("");
  const [namaLengkap, setNamaLengkap] = useState("");
  const [sandi, setSandi] = useState("");
  const [sedangKirim, setSedangKirim] = useState(false);

  async function kirim(e: FormEvent) {
    e.preventDefault();
    setSedangKirim(true);
    try {
      await minta("/pengguna", {
        metode: "POST",
        muatan: {
          nama_pengguna: namaPengguna,
          nama_lengkap: namaLengkap,
          sandi,
          peran: "kasir",
        },
      });
      onSelesai();
    } catch (e) {
      onGagal(pesanDari(e));
    } finally {
      setSedangKirim(false);
    }
  }

  return (
    <form onSubmit={kirim} className="space-y-3 rounded border border-gray-300 p-3">
      <Kolom
        label="Nama pengguna"
        value={namaPengguna}
        onChange={(e) => setNamaPengguna(e.target.value)}
      />
      <Kolom
        label="Nama lengkap"
        value={namaLengkap}
        onChange={(e) => setNamaLengkap(e.target.value)}
      />
      <Kolom
        label="Sandi"
        type="password"
        autoComplete="new-password"
        value={sandi}
        onChange={(e) => setSandi(e.target.value)}
      />
      <p className="text-sm text-gray-700">
        Akun baru selalu berperan kasir. Peran pemilik hanya bisa diberikan
        setelah akunnya ada.
      </p>
      <Tombol utama type="submit" disabled={sedangKirim}>
        {sedangKirim ? "Menyimpan..." : "Simpan"}
      </Tombol>
    </form>
  );
}
