import type { KeadaanSinkron } from "../lokal/useSinkron";

/** Bilah status kasir. Tidak pernah kosong.
 *
 * Kasir tidak boleh perlu menebak apakah pekerjaannya tersimpan
 * (bab 05 §5.6).
 */
export function BilahStatus({ keadaan }: { keadaan: KeadaanSinkron }) {
  const { daring, menunggu, gagal, peringatan, jamMeleset, sedangKirim } = keadaan;

  let warna = "bg-green-100 text-green-900";
  let teks = "Tersinkron";

  if (!daring) {
    warna = "bg-red-100 text-red-900";
    teks = menunggu > 0 ? `Offline · ${menunggu} transaksi menunggu` : "Offline";
  } else if (menunggu > 0) {
    warna = "bg-amber-100 text-amber-900";
    teks = `${menunggu} transaksi menunggu${sedangKirim ? " · mengirim" : ""}`;
  }

  return (
    <div className="space-y-1">
      <p className={`rounded px-3 py-2 text-sm font-medium ${warna}`} role="status">
        {teks}
      </p>

      {gagal > 0 && (
        <p role="alert" className="rounded bg-red-100 px-3 py-2 text-sm text-red-900">
          {gagal} transaksi ditolak server dan butuh diperiksa. Penjualan tetap
          bisa dilanjutkan.
        </p>
      )}

      {peringatan && (
        <p role="alert" className="rounded bg-amber-100 px-3 py-2 text-sm text-amber-900">
          Antrean menumpuk atau sudah lebih dari sehari belum terkirim. Periksa
          sambungan internet toko.
        </p>
      )}

      {jamMeleset && (
        <p role="alert" className="rounded bg-amber-100 px-3 py-2 text-sm text-amber-900">
          Jam komputer ini meleset lebih dari lima menit dari server. Betulkan
          jamnya, karena waktu transaksi dipakai seluruh laporan.
        </p>
      )}
    </div>
  );
}
