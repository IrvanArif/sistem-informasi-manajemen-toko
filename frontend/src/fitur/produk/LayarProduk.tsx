import { useCallback, useEffect, useState } from "react";
import type { ProdukTampil } from "../../api/domain";
import { jumlah, rupiah } from "../../api/domain";
import { KesalahanApi, minta } from "../../api/klien";
import { Kolom, PesanKesalahan, Tombol } from "../../komponen/dasar";

function pesanDari(e: unknown): string {
  return e instanceof KesalahanApi ? e.pesan : "Tidak bisa terhubung ke server";
}

export function LayarProduk({
  bolehUbah,
  onTambah,
  onImpor,
}: {
  bolehUbah: boolean;
  onTambah: () => void;
  onImpor: () => void;
}) {
  const [cari, setCari] = useState("");
  const [daftar, setDaftar] = useState<ProdukTampil[]>([]);
  const [kesalahan, setKesalahan] = useState<string | null>(null);
  const [memuat, setMemuat] = useState(true);

  const muat = useCallback(async (kata: string) => {
    setMemuat(true);
    try {
      const hasil = await minta<ProdukTampil[]>(
        `/produk?cari=${encodeURIComponent(kata)}&batas=200`,
      );
      setDaftar(hasil);
      setKesalahan(null);
    } catch (e) {
      setKesalahan(pesanDari(e));
    } finally {
      setMemuat(false);
    }
  }, []);

  // Pencarian ditunda sesaat setelah ketikan berhenti. Tanpa penundaan,
  // mengetik "indomie" mengirim tujuh permintaan dan jawaban yang datang
  // tidak berurutan bisa menampilkan hasil dari kata yang sudah usang.
  useEffect(() => {
    const jeda = setTimeout(() => void muat(cari), 250);
    return () => clearTimeout(jeda);
  }, [cari, muat]);

  return (
    <section className="p-4 max-w-4xl mx-auto space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-gray-900">Produk</h1>
        {bolehUbah && (
          <div className="flex gap-2">
            <Tombol onClick={onImpor}>Impor CSV</Tombol>
            <Tombol utama onClick={onTambah}>
              Tambah produk
            </Tombol>
          </div>
        )}
      </div>

      <Kolom
        label="Cari nama, kode, atau pindai barcode"
        autoFocus
        value={cari}
        onChange={(e) => setCari(e.target.value)}
        placeholder="indomie"
      />

      <PesanKesalahan>{kesalahan}</PesanKesalahan>

      {memuat && daftar.length === 0 ? (
        <p className="text-gray-700">Memuat...</p>
      ) : daftar.length === 0 ? (
        <p className="text-gray-700">
          {cari
            ? `Tidak ada produk yang cocok dengan "${cari}".`
            : "Belum ada produk. Mulai dengan impor CSV atau tambah satu per satu."}
        </p>
      ) : (
        <ul className="space-y-2">
          {daftar.map((p) => (
            <BarisProduk key={p.id} produk={p} />
          ))}
        </ul>
      )}
    </section>
  );
}

function BarisProduk({ produk }: { produk: ProdukTampil }) {
  const stok = Number(produk.stok);
  const minimum = Number(produk.stok_minimum);
  const dasar = produk.satuan.find((s) => s.is_dasar);

  return (
    <li className="rounded border border-gray-300 p-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-medium text-gray-900">{produk.nama}</p>
          <p className="text-sm text-gray-700">
            {produk.kode}
            {produk.perlu_dilengkapi && " · perlu dilengkapi"}
            {!produk.aktif && " · nonaktif"}
          </p>
        </div>
        <div className="text-right shrink-0">
          <p className={stok < 0 ? "font-medium text-red-700" : "font-medium text-gray-900"}>
            {jumlah(produk.stok)} {produk.satuan_dasar}
          </p>
          {stok < 0 ? (
            <p className="text-sm text-red-700">stok minus</p>
          ) : stok <= minimum && minimum > 0 ? (
            <p className="text-sm text-amber-700">menipis</p>
          ) : null}
        </div>
      </div>

      <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-700">
        {produk.satuan.map((s) => (
          <li key={s.id}>
            {s.nama} {Number(s.faktor) !== 1 && `(x${jumlah(s.faktor)})`}{" "}
            <span className="text-gray-900">{rupiah(s.harga_jual)}</span>
          </li>
        ))}
        {dasar === undefined && (
          <li className="text-red-700">tanpa satuan dasar</li>
        )}
      </ul>
    </li>
  );
}
