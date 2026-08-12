import { useState, type FormEvent } from "react";
import type { Kategori, Produk } from "../../api/domain";
import { KesalahanApi, minta } from "../../api/klien";
import { Kolom, PesanKesalahan, Tombol } from "../../komponen/dasar";

interface BarisSatuan {
  nama: string;
  faktor: string;
  harga_jual: string;
  barcode: string;
  is_dasar: boolean;
}

function satuanKosong(dasar = false): BarisSatuan {
  return { nama: "", faktor: dasar ? "1" : "", harga_jual: "", barcode: "", is_dasar: dasar };
}

export function FormProduk({
  kategori,
  onSelesai,
  onBatal,
}: {
  kategori: Kategori[];
  onSelesai: () => void;
  onBatal: () => void;
}) {
  const [kode, setKode] = useState("");
  const [nama, setNama] = useState("");
  const [kategoriId, setKategoriId] = useState("");
  const [stokAwal, setStokAwal] = useState("0");
  const [stokMinimum, setStokMinimum] = useState("0");
  const [satuan, setSatuan] = useState<BarisSatuan[]>([satuanKosong(true)]);
  const [kesalahan, setKesalahan] = useState<string | null>(null);
  const [sedangKirim, setSedangKirim] = useState(false);

  const dasar = satuan.find((s) => s.is_dasar);

  function ubahSatuan(i: number, ubah: Partial<BarisSatuan>) {
    setSatuan((lama) => lama.map((s, j) => (i === j ? { ...s, ...ubah } : s)));
  }

  function jadikanDasar(i: number) {
    // Tepat satu satuan dasar. Ditegakkan juga di sini supaya kesalahannya
    // ketahuan sebelum dikirim, bukan setelah ditolak server.
    setSatuan((lama) =>
      lama.map((s, j) => ({ ...s, is_dasar: i === j, faktor: i === j ? "1" : s.faktor })),
    );
  }

  async function kirim(e: FormEvent) {
    e.preventDefault();
    setKesalahan(null);
    setSedangKirim(true);
    try {
      await minta("/produk", {
        metode: "POST",
        muatan: {
          kode,
          nama,
          kategori_id: kategoriId ? Number(kategoriId) : null,
          satuan_dasar: dasar?.nama ?? "",
          stok_awal: stokAwal || "0",
          stok_minimum: stokMinimum || "0",
          satuan: satuan.map((s) => ({
            nama: s.nama,
            faktor: s.faktor || "1",
            harga_jual: Number(s.harga_jual || 0),
            barcode: s.barcode || null,
            is_dasar: s.is_dasar,
          })),
        },
      });
      onSelesai();
    } catch (e) {
      setKesalahan(e instanceof KesalahanApi ? e.pesan : "Tidak bisa terhubung ke server");
    } finally {
      setSedangKirim(false);
    }
  }

  return (
    <form onSubmit={kirim} className="p-4 max-w-2xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">Produk baru</h1>

      <div className="grid gap-4 sm:grid-cols-2">
        <Kolom label="Kode" value={kode} onChange={(e) => setKode(e.target.value)} />
        <Kolom label="Nama" value={nama} onChange={(e) => setNama(e.target.value)} />
      </div>

      <label className="block">
        <span className="text-sm font-medium text-gray-900">Kategori</span>
        <select
          value={kategoriId}
          onChange={(e) => setKategoriId(e.target.value)}
          className="mt-1 w-full min-h-11 rounded border border-gray-400 px-3 py-2 text-gray-900"
        >
          <option value="">Tanpa kategori</option>
          {kategori.map((k) => (
            <option key={k.id} value={k.id}>
              {k.nama}
            </option>
          ))}
        </select>
      </label>

      <div className="grid gap-4 sm:grid-cols-2">
        <Kolom
          label={`Stok awal (${dasar?.nama || "satuan dasar"})`}
          inputMode="decimal"
          value={stokAwal}
          onChange={(e) => setStokAwal(e.target.value)}
        />
        <Kolom
          label="Stok minimum"
          inputMode="decimal"
          value={stokMinimum}
          onChange={(e) => setStokMinimum(e.target.value)}
        />
      </div>

      <fieldset className="space-y-3 rounded border border-gray-300 p-3">
        <legend className="px-1 text-sm font-medium text-gray-900">Satuan</legend>
        <p className="text-sm text-gray-700">
          Satuan dasar adalah yang terkecil, tempat stok dihitung. Harga tiap
          satuan ditulis sendiri, bukan kelipatan: satu dus boleh lebih murah
          daripada empat puluh bungkus.
        </p>

        {satuan.map((s, i) => (
          <div key={i} className="grid gap-2 sm:grid-cols-[1fr_5rem_7rem_1fr_auto] sm:items-end">
            <Kolom label="Nama" value={s.nama} onChange={(e) => ubahSatuan(i, { nama: e.target.value })} />
            <Kolom
              label="Faktor"
              inputMode="decimal"
              disabled={s.is_dasar}
              value={s.faktor}
              onChange={(e) => ubahSatuan(i, { faktor: e.target.value })}
            />
            <Kolom
              label="Harga"
              inputMode="numeric"
              value={s.harga_jual}
              onChange={(e) => ubahSatuan(i, { harga_jual: e.target.value })}
            />
            <Kolom label="Barcode" value={s.barcode} onChange={(e) => ubahSatuan(i, { barcode: e.target.value })} />
            <label className="flex min-h-11 items-center gap-2 text-sm text-gray-900">
              <input
                type="radio"
                name="satuan-dasar"
                checked={s.is_dasar}
                onChange={() => jadikanDasar(i)}
              />
              dasar
            </label>
          </div>
        ))}

        <Tombol type="button" onClick={() => setSatuan((l) => [...l, satuanKosong()])}>
          Tambah satuan
        </Tombol>
      </fieldset>

      <PesanKesalahan>{kesalahan}</PesanKesalahan>

      <div className="flex gap-2">
        <Tombol utama type="submit" disabled={sedangKirim}>
          {sedangKirim ? "Menyimpan..." : "Simpan"}
        </Tombol>
        <Tombol type="button" onClick={onBatal}>
          Batal
        </Tombol>
      </div>
    </form>
  );
}

export type { Produk };
