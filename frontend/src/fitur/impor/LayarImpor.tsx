import { useState } from "react";
import type { HasilImpor } from "../../api/domain";
import { KesalahanApi, ambilTokenAkses } from "../../api/klien";
import { PesanKesalahan, Tombol } from "../../komponen/dasar";

const DASAR = import.meta.env.VITE_API_DASAR ?? "http://localhost:8000/api/v1";

async function unggah(jalur: string, berkas: File): Promise<HasilImpor> {
  const isi = new FormData();
  isi.append("berkas", berkas);
  const jawaban = await fetch(`${DASAR}${jalur}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${ambilTokenAkses() ?? ""}` },
    body: isi,
  });
  const data = (await jawaban.json().catch(() => null)) as
    | (HasilImpor & { kode?: string; pesan?: string })
    | null;
  if (!jawaban.ok) {
    throw new KesalahanApi(
      data?.kode ?? "KESALAHAN_TIDAK_DIKENAL",
      data?.pesan ?? "Berkas tidak bisa diproses",
      jawaban.status,
    );
  }
  return data as HasilImpor;
}

export function LayarImpor({ onSelesai }: { onSelesai: () => void }) {
  const [berkas, setBerkas] = useState<File | null>(null);
  const [pratinjau, setPratinjau] = useState<HasilImpor | null>(null);
  const [hasil, setHasil] = useState<HasilImpor | null>(null);
  const [kesalahan, setKesalahan] = useState<string | null>(null);
  const [sibuk, setSibuk] = useState(false);

  function pesanDari(e: unknown): string {
    return e instanceof KesalahanApi ? e.pesan : "Tidak bisa terhubung ke server";
  }

  async function jalankan(jalur: string, simpan: (h: HasilImpor) => void) {
    if (!berkas) return;
    setKesalahan(null);
    setSibuk(true);
    try {
      simpan(await unggah(jalur, berkas));
    } catch (e) {
      setKesalahan(pesanDari(e));
    } finally {
      setSibuk(false);
    }
  }

  return (
    <section className="p-4 max-w-2xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">Impor produk dari CSV</h1>

      <p className="text-gray-700">
        Berkas boleh berpemisah koma maupun titik koma, sehingga hasil ekspor
        dari lembar kerja berbahasa Indonesia bisa dipakai apa adanya.
      </p>

      <a
        href={`${DASAR}/produk/impor/contoh`}
        className="inline-block text-gray-900 underline"
      >
        Unduh berkas contoh
      </a>

      <label className="block">
        <span className="text-sm font-medium text-gray-900">Berkas CSV</span>
        <input
          type="file"
          accept=".csv,text/csv"
          onChange={(e) => {
            setBerkas(e.target.files?.[0] ?? null);
            setPratinjau(null);
            setHasil(null);
          }}
          className="mt-1 block w-full text-gray-900"
        />
      </label>

      <PesanKesalahan>{kesalahan}</PesanKesalahan>

      <div className="flex flex-wrap gap-2">
        <Tombol
          disabled={!berkas || sibuk}
          onClick={() => void jalankan("/produk/impor/pratinjau", setPratinjau)}
        >
          {sibuk ? "Memeriksa..." : "Periksa dulu"}
        </Tombol>
        <Tombol
          utama
          disabled={!pratinjau || sibuk}
          onClick={() => void jalankan("/produk/impor/jalankan", setHasil)}
        >
          Jalankan impor
        </Tombol>
      </div>

      {pratinjau && !hasil && <Ringkasan judul="Hasil pemeriksaan" hasil={pratinjau} />}
      {hasil && (
        <>
          <Ringkasan judul="Hasil impor" hasil={hasil} />
          <Tombol utama onClick={onSelesai}>
            Lihat daftar produk
          </Tombol>
        </>
      )}
    </section>
  );
}

function Ringkasan({ judul, hasil }: { judul: string; hasil: HasilImpor }) {
  return (
    <div className="rounded border border-gray-300 p-3 space-y-2">
      <h2 className="font-medium text-gray-900">{judul}</h2>
      <p className="text-gray-900">
        {hasil.tersimpan > 0
          ? `${hasil.tersimpan} produk tersimpan`
          : `${hasil.sah} baris siap disimpan`}
        {hasil.gagal.length > 0 && `, ${hasil.gagal.length} baris gagal`}
      </p>

      {hasil.gagal.length > 0 && (
        <>
          <p className="text-sm text-gray-700">
            Baris yang gagal dilewati, sisanya tetap tersimpan. Betulkan baris
            berikut lalu unggah ulang berkasnya.
          </p>
          <ul className="space-y-1 text-sm">
            {hasil.gagal.map((g) => (
              <li key={g.baris} className="text-red-700">
                Baris {g.baris}: {g.alasan}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
