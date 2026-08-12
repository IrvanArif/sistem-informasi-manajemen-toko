import { useCallback, useEffect, useRef, useState } from "react";
import type { Penjualan, ProdukTampil, SesiKas } from "../../api/domain";
import { jumlah as tulisJumlah, rupiah } from "../../api/domain";
import { KesalahanApi, minta } from "../../api/klien";
import { Kolom, PesanKesalahan, Tombol } from "../../komponen/dasar";
import {
  bacaJumlah,
  nomorNotaBaru,
  subtotalBaris,
  subtotalKeranjang,
  type BarisKeranjang,
} from "./keranjang";
import { DialogBayar } from "./DialogBayar";

function pesanDari(e: unknown): string {
  return e instanceof KesalahanApi ? e.pesan : "Tidak bisa terhubung ke server";
}

export function LayarKasir({ sesi, onSesiBerubah }: { sesi: SesiKas; onSesiBerubah: () => void }) {
  const [cari, setCari] = useState("");
  const [hasil, setHasil] = useState<ProdukTampil[]>([]);
  const [isi, setIsi] = useState<BarisKeranjang[]>([]);
  const [bayarTampil, setBayarTampil] = useState(false);
  const [kesalahan, setKesalahan] = useState<string | null>(null);
  const [selesai, setSelesai] = useState<Penjualan | null>(null);
  const kolomCari = useRef<HTMLInputElement>(null);

  // Fokus selalu kembali ke kolom cari. Kasir tidak pernah perlu mengklik
  // untuk melanjutkan, dan scanner barcode, yang bekerja persis seperti
  // papan ketik, langsung berfungsi tanpa penyesuaian (bab 06 §6.3).
  const fokuskanCari = useCallback(() => kolomCari.current?.focus(), []);

  useEffect(() => {
    if (!cari.trim()) {
      setHasil([]);
      return;
    }
    const jeda = setTimeout(() => {
      void minta<ProdukTampil[]>(`/produk?cari=${encodeURIComponent(cari)}&batas=8`)
        .then(setHasil)
        .catch((e) => setKesalahan(pesanDari(e)));
    }, 200);
    return () => clearTimeout(jeda);
  }, [cari]);

  function tambah(produk: ProdukTampil, satuanId?: number) {
    const satuan = produk.satuan.find((s) => s.id === satuanId) ??
      produk.satuan.find((s) => s.is_dasar) ?? produk.satuan[0];
    if (!satuan) return;

    setIsi((lama) => [
      ...lama,
      { kunci: `${Date.now()}-${satuan.id}`, produk, satuan, jumlah: 1, diskon: 0 },
    ]);
    setCari("");
    setHasil([]);
    fokuskanCari();
  }

  function ubahJumlah(kunci: string, teks: string) {
    const n = bacaJumlah(teks);
    if (n === null) return;
    setIsi((lama) => lama.map((b) => (b.kunci === kunci ? { ...b, jumlah: n } : b)));
  }

  function hapusTerakhir() {
    setIsi((lama) => lama.slice(0, -1));
    fokuskanCari();
  }

  // Pintasan F-key. Setiap tindakan juga punya tombol di layar, sehingga
  // alur yang sama bisa diselesaikan dengan sentuhan (bab 06 aturan #6).
  useEffect(() => {
    function tekan(e: KeyboardEvent) {
      if (e.key === "F9" && isi.length > 0) {
        e.preventDefault();
        setBayarTampil(true);
      } else if (e.key === "F3") {
        e.preventDefault();
        hapusTerakhir();
      } else if (e.key === "Escape") {
        e.preventDefault();
        setBayarTampil(false);
        fokuskanCari();
      }
    }
    window.addEventListener("keydown", tekan);
    return () => window.removeEventListener("keydown", tekan);
  }, [isi.length, fokuskanCari]);

  async function simpan(dibayar: number, metode: "tunai" | "transfer" | "qris") {
    const total = subtotalKeranjang(isi);
    try {
      const nota = await minta<Penjualan>("/penjualan", {
        metode: "POST",
        muatan: {
          uuid_klien: crypto.randomUUID(),
          nomor_nota: nomorNotaBaru(),
          waktu_transaksi: new Date().toISOString(),
          metode_bayar: metode,
          diskon_nota: 0,
          pembulatan: 0,
          total,
          dibayar,
          kembalian: Math.max(0, dibayar - total),
          item: isi.map((b) => ({
            produk_id: b.produk.id,
            satuan_id: b.satuan.id,
            jumlah: String(b.jumlah),
            harga_satuan: b.satuan.harga_jual,
            diskon: b.diskon,
            subtotal: subtotalBaris(b),
          })),
        },
      });
      setSelesai(nota);
      setIsi([]);
      setBayarTampil(false);
      onSesiBerubah();
    } catch (e) {
      setKesalahan(pesanDari(e));
      setBayarTampil(false);
    }
  }

  const total = subtotalKeranjang(isi);

  if (selesai) {
    return (
      <SetelahBayar
        nota={selesai}
        onLanjut={() => {
          setSelesai(null);
          fokuskanCari();
        }}
      />
    );
  }

  return (
    <section className="p-4 max-w-5xl mx-auto space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-gray-700">
        <span>Sesi #{sesi.id} · modal {rupiah(sesi.modal_awal)}</span>
      </div>

      <Kolom
        ref={kolomCari}
        label="Cari atau pindai barcode"
        autoFocus
        value={cari}
        onChange={(e) => setCari(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && hasil.length > 0) {
            e.preventDefault();
            tambah(hasil[0]);
          }
        }}
      />

      {hasil.length > 0 && (
        <ul className="rounded border border-gray-300 divide-y divide-gray-200">
          {hasil.map((p) => (
            <li key={p.id} className="p-2">
              <p className="font-medium text-gray-900">{p.nama}</p>
              <div className="mt-1 flex flex-wrap gap-2">
                {p.satuan.map((s) => (
                  <Tombol key={s.id} onClick={() => tambah(p, s.id)}>
                    {s.nama} · {rupiah(s.harga_jual)}
                  </Tombol>
                ))}
              </div>
            </li>
          ))}
        </ul>
      )}

      <PesanKesalahan>{kesalahan}</PesanKesalahan>

      <div className="grid gap-4 lg:grid-cols-[1fr_18rem]">
        <ul className="space-y-2">
          {isi.length === 0 && <li className="text-gray-700">Keranjang kosong.</li>}
          {isi.map((b) => (
            <li key={b.kunci} className="flex flex-wrap items-center justify-between gap-2
                                         rounded border border-gray-300 p-2">
              <div className="min-w-0">
                <p className="font-medium text-gray-900">{b.produk.nama}</p>
                <p className="text-sm text-gray-700">
                  {b.satuan.nama} · {rupiah(b.satuan.harga_jual)}
                </p>
              </div>
              <input
                aria-label={`Jumlah ${b.produk.nama}`}
                inputMode="decimal"
                defaultValue={b.jumlah}
                onChange={(e) => ubahJumlah(b.kunci, e.target.value)}
                className="w-20 min-h-11 rounded border border-gray-400 px-2 text-right text-gray-900"
              />
              <span className="w-28 text-right font-medium text-gray-900">
                {rupiah(subtotalBaris(b))}
              </span>
            </li>
          ))}
        </ul>

        <aside className="space-y-3 rounded border border-gray-300 p-3 h-fit">
          <p className="text-sm text-gray-700">TOTAL</p>
          <p className="text-3xl font-bold text-gray-900">{rupiah(total)}</p>
          <p className="text-sm text-gray-700">
            {isi.length} baris ·{" "}
            {tulisJumlah(String(isi.reduce((n, b) => n + b.jumlah, 0)))} item
          </p>
          <Tombol utama className="w-full" disabled={isi.length === 0}
                  onClick={() => setBayarTampil(true)}>
            F9 · BAYAR
          </Tombol>
          <Tombol className="w-full" disabled={isi.length === 0} onClick={hapusTerakhir}>
            F3 · Hapus baris terakhir
          </Tombol>
        </aside>
      </div>

      {bayarTampil && (
        <DialogBayar
          total={total}
          onBatal={() => {
            setBayarTampil(false);
            fokuskanCari();
          }}
          onBayar={(dibayar, metode) => void simpan(dibayar, metode)}
        />
      )}
    </section>
  );
}

function SetelahBayar({ nota, onLanjut }: { nota: Penjualan; onLanjut: () => void }) {
  useEffect(() => {
    function tekan(e: KeyboardEvent) {
      if (e.key === "Enter") onLanjut();
    }
    window.addEventListener("keydown", tekan);
    return () => window.removeEventListener("keydown", tekan);
  }, [onLanjut]);

  return (
    <section className="p-4 max-w-md mx-auto space-y-4 text-center">
      <p className="text-gray-700">Nota {nota.nomor_nota} tersimpan</p>
      <p className="text-sm text-gray-700">KEMBALIAN</p>
      <p className="text-5xl font-bold text-gray-900">{rupiah(nota.kembalian)}</p>
      <Tombol utama className="w-full" onClick={onLanjut}>
        Enter · Transaksi baru
      </Tombol>
    </section>
  );
}
