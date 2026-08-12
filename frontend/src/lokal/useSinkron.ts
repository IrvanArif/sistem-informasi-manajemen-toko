import { useCallback, useEffect, useState } from "react";
import {
  jedaBerikutnya,
  jumlahGagal,
  jumlahMenunggu,
  kirimAntrean,
  perluDiperingatkan,
  tertuaMenunggu,
} from "./antrean";
import { mintaPenyimpananPermanen } from "./basisdata";
import { jamMelesetJauh, sinkronKatalog } from "./replika";

export interface KeadaanSinkron {
  daring: boolean;
  menunggu: number;
  gagal: number;
  peringatan: boolean;
  jamMeleset: boolean;
  sedangKirim: boolean;
}

const SELANG_KATALOG_MENIT = 15;

/** Mengurus sinkronisasi katalog dan pengiriman antrean di latar.
 *
 * Pengiriman dipicu tiga hal: saat aplikasi dibuka, saat browser
 * mengabarkan koneksi pulih, dan lewat jeda menaik bila masih gagal.
 */
export function useSinkron(aktif: boolean) {
  const [keadaan, setKeadaan] = useState<KeadaanSinkron>({
    daring: navigator.onLine,
    menunggu: 0,
    gagal: 0,
    peringatan: false,
    jamMeleset: false,
    sedangKirim: false,
  });

  const segarkanHitungan = useCallback(async () => {
    const [menunggu, gagal, tertua, meleset] = await Promise.all([
      jumlahMenunggu(),
      jumlahGagal(),
      tertuaMenunggu(),
      jamMelesetJauh(),
    ]);
    setKeadaan((l) => ({
      ...l,
      menunggu,
      gagal,
      peringatan: perluDiperingatkan(menunggu, tertua),
      jamMeleset: meleset,
    }));
  }, []);

  const kirim = useCallback(async (): Promise<number> => {
    setKeadaan((l) => ({ ...l, sedangKirim: true }));
    try {
      const hasil = await kirimAntrean();
      await segarkanHitungan();
      // Status daring ditentukan oleh hasil permintaan yang sungguhan,
      // bukan oleh navigator.onLine. Browser melaporkan "online" selama
      // komputer terhubung ke router, bahkan ketika ISP-nya mati, dan
      // itulah bentuk gangguan yang paling sering terjadi di toko.
      if (hasil.terkirim > 0 || hasil.jaringanGagal) {
        setKeadaan((l) => ({ ...l, daring: !hasil.jaringanGagal }));
      }
      return hasil.tersisa;
    } finally {
      setKeadaan((l) => ({ ...l, sedangKirim: false }));
    }
  }, [segarkanHitungan]);

  // Perubahan status jaringan. Koneksi pulih langsung memicu pengiriman,
  // tanpa menunggu jeda berikutnya.
  useEffect(() => {
    function daring() {
      setKeadaan((l) => ({ ...l, daring: true }));
      void kirim();
    }
    function luring() {
      setKeadaan((l) => ({ ...l, daring: false }));
    }
    window.addEventListener("online", daring);
    window.addEventListener("offline", luring);
    return () => {
      window.removeEventListener("online", daring);
      window.removeEventListener("offline", luring);
    };
  }, [kirim]);

  // Pengiriman berjeda menaik. Percobaan yang gagal menunggu lebih lama,
  // sehingga server yang sedang bermasalah tidak dibebani terus-menerus.
  useEffect(() => {
    if (!aktif) return;
    let percobaan = 0;
    let waktu: number;

    const jalan = async () => {
      if (navigator.onLine) {
        const tersisa = await kirim();
        percobaan = tersisa > 0 ? percobaan + 1 : 0;
      }
      waktu = window.setTimeout(() => void jalan(), jedaBerikutnya(percobaan) * 1000);
    };

    void jalan();
    return () => clearTimeout(waktu);
  }, [aktif, kirim]);

  // Katalog disegarkan saat dibuka dan berkala selama daring.
  useEffect(() => {
    if (!aktif) return;
    // Sinkron katalog sekaligus menjadi penduga sambungan saat antrean
    // kosong: kalau ia berhasil, server benar-benar terjangkau.
    const tarik = () => {
      void sinkronKatalog()
        .then(async () => {
          setKeadaan((l) => ({ ...l, daring: true }));
          await segarkanHitungan();
        })
        .catch(() => setKeadaan((l) => ({ ...l, daring: false })));
    };
    tarik();
    const selang = window.setInterval(tarik, SELANG_KATALOG_MENIT * 60 * 1000);
    return () => clearInterval(selang);
  }, [aktif, segarkanHitungan]);

  useEffect(() => {
    if (aktif) void mintaPenyimpananPermanen();
  }, [aktif]);

  return { keadaan, kirim, segarkanHitungan };
}
