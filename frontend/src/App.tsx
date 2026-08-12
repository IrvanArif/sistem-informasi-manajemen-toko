import { useCallback, useEffect, useState } from "react";
import type { Kategori, Pengguna, SesiKas } from "./api/domain";
import { KesalahanApi, hapusToken, minta, sudahMasuk } from "./api/klien";
import { LayarImpor } from "./fitur/impor/LayarImpor";
import { LayarKasir } from "./fitur/kasir/LayarKasir";
import { BukaSesiKas, TutupSesiKas } from "./fitur/kasir/LayarSesiKas";
import { LayarMasuk } from "./fitur/masuk/LayarMasuk";
import { LayarPengguna } from "./fitur/pengguna/LayarPengguna";
import { FormProduk } from "./fitur/produk/FormProduk";
import { LayarProduk } from "./fitur/produk/LayarProduk";
import { Tombol } from "./komponen/dasar";
import { bacaMeta, tulisMeta } from "./lokal/basisdata";
import { useSinkron } from "./lokal/useSinkron";

type Halaman = "kasir" | "tutup-kas" | "produk" | "produk-baru" | "impor" | "pengguna";

export default function App() {
  const [saya, setSaya] = useState<Pengguna | null>(null);
  const [memeriksa, setMemeriksa] = useState(true);
  const [halaman, setHalaman] = useState<Halaman>("kasir");
  const [kategori, setKategori] = useState<Kategori[]>([]);
  const [sesiKas, setSesiKas] = useState<SesiKas | null>(null);
  // Sesi kas belum diketahui bukanlah sama dengan sesi kas tidak ada.
  // Tanpa pembeda ini, form "Buka sesi kas" sempat tampil padahal sesinya
  // sedang terbuka, dan kasir bisa mengisi modal awal untuk sesi yang
  // sudah jalan.
  const [kasDiperiksa, setKasDiperiksa] = useState(false);
  const { keadaan, kirim } = useSinkron(saya !== null);

  const periksaSesi = useCallback(async () => {
    if (!sudahMasuk()) {
      setSaya(null);
      setMemeriksa(false);
      return;
    }
    try {
      const pengguna = await minta<Pengguna>("/auth/saya");
      setSaya(pengguna);
      await tulisMeta("pengguna", JSON.stringify(pengguna));
    } catch (e) {
      // Hanya 401 yang berarti sesinya benar-benar berakhir. Kegagalan
      // jaringan TIDAK boleh mengeluarkan pengguna: masuk kembali menuntut
      // server, sehingga kasir yang terusir saat internet mati tidak punya
      // jalan kembali, dan seluruh kemampuan offline runtuh hanya karena
      // halaman disegarkan.
      if (e instanceof KesalahanApi && e.status === 401) {
        hapusToken();
        await tulisMeta("pengguna", "");
        setSaya(null);
      } else {
        const tersimpan = await bacaMeta("pengguna");
        if (tersimpan) setSaya(JSON.parse(tersimpan) as Pengguna);
      }
    } finally {
      setMemeriksa(false);
    }
  }, []);

  const muatSesiKas = useCallback(async () => {
    try {
      const kas = await minta<SesiKas | null>("/sesi-kas/aktif");
      setSesiKas(kas);
      setKasDiperiksa(true);
      await tulisMeta("sesi_kas_aktif", kas ? JSON.stringify(kas) : "");
      return;
    } catch (e) {
      // Kegagalan jaringan TIDAK berarti sesi kasnya hilang. Menghapusnya
      // di sini akan melempar kasir kembali ke layar buka sesi setiap kali
      // internet putus, persis saat ia paling butuh terus melayani.
      // Hanya sesi yang sudah berakhir yang boleh mengosongkannya.
      if (e instanceof KesalahanApi && e.status === 401) {
        setSesiKas(null);
        setKasDiperiksa(true);
        return;
      }
    }
    // Offline: pakai sesi yang terakhir diketahui, supaya layar kasir tetap
    // terbuka bahkan setelah halaman dimuat ulang tanpa internet.
    const tersimpan = await bacaMeta("sesi_kas_aktif");
    if (tersimpan) setSesiKas(JSON.parse(tersimpan) as SesiKas);
    setKasDiperiksa(true);
  }, []);

  useEffect(() => {
    void periksaSesi();
  }, [periksaSesi]);

  useEffect(() => {
    if (!saya) return;
    void muatSesiKas();
    void minta<Kategori[]>("/kategori").then(setKategori).catch(() => setKategori([]));
  }, [saya, muatSesiKas]);

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
          <div className="flex gap-2">
            {sesiKas && (
              <Tombol onClick={() => setHalaman("tutup-kas")}>Tutup kasir</Tombol>
            )}
            <Tombol
              onClick={() => {
                hapusToken();
                void tulisMeta("pengguna", "");
                void tulisMeta("sesi_kas_aktif", "");
                setSaya(null);
                setSesiKas(null);
              }}
            >
              Keluar
            </Tombol>
          </div>
        </div>

        <nav className="flex flex-wrap gap-2 px-4 pb-3">
          <Menu aktif={halaman === "kasir" || halaman === "tutup-kas"}
                onClick={() => setHalaman("kasir")}>
            Kasir
          </Menu>
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

      {halaman === "kasir" && !kasDiperiksa && (
        <main className="p-4 text-gray-700">Memuat sesi kas...</main>
      )}

      {halaman === "kasir" &&
        kasDiperiksa &&
        (sesiKas ? (
          <LayarKasir
            sesi={sesiKas}
            onSesiBerubah={() => void muatSesiKas()}
            keadaan={keadaan}
            kirimAntrean={kirim}
          />
        ) : (
          <BukaSesiKas onDibuka={() => void muatSesiKas()} />
        ))}

      {halaman === "tutup-kas" && sesiKas && (
        <TutupSesiKas
          sesi={sesiKas}
          onDitutup={() => {
            setSesiKas(null);
            setHalaman("kasir");
          }}
          onBatal={() => setHalaman("kasir")}
        />
      )}

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
