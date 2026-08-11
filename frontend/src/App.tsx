import { useCallback, useEffect, useState } from "react";
import type { Pengguna } from "./api/domain";
import { hapusToken, minta, sudahMasuk } from "./api/klien";
import { LayarMasuk } from "./fitur/masuk/LayarMasuk";
import { LayarPengguna } from "./fitur/pengguna/LayarPengguna";
import { Tombol } from "./komponen/dasar";

export default function App() {
  const [saya, setSaya] = useState<Pengguna | null>(null);
  const [memeriksa, setMemeriksa] = useState(true);

  const periksaSesi = useCallback(async () => {
    if (!sudahMasuk()) {
      setSaya(null);
      setMemeriksa(false);
      return;
    }
    try {
      setSaya(await minta<Pengguna>("/auth/saya"));
    } catch {
      hapusToken();
      setSaya(null);
    } finally {
      setMemeriksa(false);
    }
  }, []);

  useEffect(() => {
    void periksaSesi();
  }, [periksaSesi]);

  if (memeriksa) {
    return <main className="p-4 text-gray-700">Memuat...</main>;
  }

  if (!saya) {
    return <LayarMasuk onBerhasil={() => void periksaSesi()} />;
  }

  return (
    <div className="min-h-screen">
      <header
        className="flex flex-wrap items-center justify-between gap-3 border-b
                   border-gray-300 p-4"
      >
        <div>
          <p className="font-medium text-gray-900">{saya.nama_lengkap}</p>
          <p className="text-sm text-gray-700">{saya.peran}</p>
        </div>
        <Tombol
          onClick={() => {
            hapusToken();
            setSaya(null);
          }}
        >
          Keluar
        </Tombol>
      </header>

      {saya.peran === "pemilik" ? (
        <LayarPengguna saya={saya} />
      ) : (
        <main className="p-4 max-w-2xl mx-auto">
          <h1 className="text-2xl font-bold text-gray-900">Selamat datang</h1>
          <p className="mt-2 text-gray-700">
            Layar kasir belum tersedia. Ia dibangun di tahap M2.
          </p>
        </main>
      )}
    </div>
  );
}
