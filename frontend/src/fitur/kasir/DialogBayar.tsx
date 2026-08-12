import { useEffect, useRef, useState } from "react";
import { rupiah } from "../../api/domain";
import { Tombol } from "../../komponen/dasar";

const PECAHAN = [5_000, 10_000, 20_000, 50_000, 100_000];

export function DialogBayar({
  total,
  onBayar,
  onBatal,
}: {
  total: number;
  onBayar: (dibayar: number, metode: "tunai" | "transfer" | "qris") => void;
  onBatal: () => void;
}) {
  const [teks, setTeks] = useState(String(total));
  const [metode, setMetode] = useState<"tunai" | "transfer" | "qris">("tunai");
  const kolom = useRef<HTMLInputElement>(null);

  useEffect(() => kolom.current?.select(), []);

  const dibayar = Number(teks.replace(/\D/g, "")) || 0;
  // Kembalian dihitung saat diketik, bukan setelah dikonfirmasi. Kasir
  // sering mengambil uang kembalian sebelum menekan tombol terakhir.
  const kembalian = dibayar - total;
  const cukup = dibayar >= total;

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-sm space-y-4 rounded bg-white p-4">
        <div>
          <p className="text-sm text-gray-700">Total</p>
          <p className="text-3xl font-bold text-gray-900">{rupiah(total)}</p>
        </div>

        <label className="block">
          <span className="text-sm font-medium text-gray-900">Uang diterima</span>
          <input
            ref={kolom}
            inputMode="numeric"
            value={teks}
            onChange={(e) => setTeks(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && cukup) onBayar(dibayar, metode);
            }}
            className="mt-1 w-full min-h-11 rounded border border-gray-400 px-3 py-2
                       text-right text-2xl text-gray-900"
          />
        </label>

        <div className="flex flex-wrap gap-2">
          <Tombol onClick={() => setTeks(String(total))}>Uang pas</Tombol>
          {PECAHAN.filter((p) => p >= total).slice(0, 3).map((p) => (
            <Tombol key={p} onClick={() => setTeks(String(p))}>
              {rupiah(p)}
            </Tombol>
          ))}
        </div>

        <div>
          <p className="text-sm text-gray-700">Kembalian</p>
          <p className={"text-2xl font-bold " + (cukup ? "text-gray-900" : "text-red-700")}>
            {cukup ? rupiah(kembalian) : "uang belum cukup"}
          </p>
        </div>

        <fieldset className="flex flex-wrap gap-3 text-gray-900">
          <legend className="text-sm font-medium">Metode</legend>
          {(["tunai", "transfer", "qris"] as const).map((m) => (
            <label key={m} className="flex items-center gap-1">
              <input
                type="radio"
                name="metode"
                checked={metode === m}
                onChange={() => setMetode(m)}
              />
              {m}
            </label>
          ))}
        </fieldset>

        <div className="flex gap-2">
          <Tombol utama className="flex-1" disabled={!cukup}
                  onClick={() => onBayar(dibayar, metode)}>
            Enter · Selesai
          </Tombol>
          <Tombol onClick={onBatal}>Esc · Batal</Tombol>
        </div>
      </div>
    </div>
  );
}
