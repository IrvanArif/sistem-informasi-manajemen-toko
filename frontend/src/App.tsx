import { useCallback, useEffect, useState } from "react";
import type { Kategori, Pengguna } from "./api/domain";
import { hapusToken, minta, sudahMasuk } from "./api/klien";
import { LayarImpor } from "./fitur/impor/LayarImpor";
import { LayarMasuk } from "./fitur/masuk/LayarMasuk";
import { LayarPengguna } from "./fitur/pengguna/LayarPengguna";
import { FormProduk } from "./fitur/produk/FormProduk";
import { LayarProduk } from "./fitur/produk/LayarProduk";
import { Tombol } from "./komponen/dasar";

type Halaman = "produk" | "produk-baru" | "impor" | "pengguna";

export default function App() {
  const [saya, setSaya] = useState<Pengguna | null>(null);
  const [memeriksa, setMemeriksa] = useState(true);
  const [halaman, setHalaman] = useState<Halaman>("produk");
  const [kategori, setKategori] = useState<Kategori[]>([]);

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

  useEffect(() => {
    if (!saya) return;
    void minta<Kategori[]>("/kategori")
      .then(setKategori)
      .catch(() => setKategori([]));
  }, [saya]);

  if (memeriksa) return <main className="p-4 text-gray-700">Memuat...</main>;
  if (!saya) return <LayarMasuk onBerhasil={() => void periksaSesi()} />;

  const pemilik = saya.peran === "pemilik";

  return (
    <div className="min-h-screen">
      <header className="border-b border-gray-300">
        <div className="flex flex-wrap items-center justify-between gap-3 p-4">
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
        </div>

        <nav className="flex flex-wrap gap-2 px-4 pb-3">
          <Menu aktif={halaman.startsWith("produk") || halaman === "impor"}
                onClick={() => setHalaman("produk")}>
            Produk
          </Menu>
          {pemilik && (
            <Menu aktif={halaman === "pengguna"} onClick={() => setHalaman("pengguna")}>
              Pengguna
            </Menu>
          )}
        </nav>
      </header>

      {halaman === "produk" && (
        <LayarProduk
          bolehUbah={pemilik}
          onTambah={() => setHalaman("produk-baru")}
          onImpor={() => setHalaman("impor")}
        />
      )}
      {halaman === "produk-baru" && (
        <FormProduk
          kategori={kategori}
          onSelesai={() => setHalaman("produk")}
          onBatal={() => setHalaman("produk")}
        />
      )}
      {halaman === "impor" && <LayarImpor onSelesai={() => setHalaman("produk")} />}
      {halaman === "pengguna" && <LayarPengguna saya={saya} />}
    </div>
  );
}

function Menu({
  aktif,
  onClick,
  children,
}: {
  aktif: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={
        "min-h-11 rounded px-4 py-2 " +
        (aktif
          ? "bg-gray-900 text-white"
          : "border border-gray-400 text-gray-900 hover:bg-gray-50")
      }
    >
      {children}
    </button>
  );
}
