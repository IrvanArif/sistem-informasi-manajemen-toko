import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  RefObject,
} from "react";

/** Tinggi minimum 44px: ukuran sasaran sentuh yang nyaman di HP (NF-07). */
const TOMBOL_DASAR =
  "min-h-11 rounded px-4 py-2 font-medium disabled:opacity-50 " +
  "disabled:cursor-not-allowed focus-visible:outline-2 focus-visible:outline-offset-2";

export function Tombol({
  utama,
  className = "",
  ...sisa
}: ButtonHTMLAttributes<HTMLButtonElement> & { utama?: boolean }) {
  const warna = utama
    ? "bg-gray-900 text-white hover:bg-gray-800"
    : "border border-gray-400 text-gray-900 hover:bg-gray-50";
  return <button className={`${TOMBOL_DASAR} ${warna} ${className}`} {...sisa} />;
}

/** ref diteruskan agar layar kasir bisa mengembalikan fokus ke kolom cari
 *  setelah tiap barang masuk keranjang. Di React 19, ref cukup diterima
 *  sebagai properti biasa. */
export function Kolom({
  label,
  ref,
  ...sisa
}: InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  ref?: RefObject<HTMLInputElement | null>;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-gray-900">{label}</span>
      <input
        ref={ref}
        className="mt-1 w-full min-h-11 rounded border border-gray-400 px-3 py-2
                   text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2"
        {...sisa}
      />
    </label>
  );
}

/** Pesan kesalahan. Memakai role alert supaya pembaca layar mengumumkannya. */
export function PesanKesalahan({ children }: { children: ReactNode }) {
  if (!children) return null;
  return (
    <p role="alert" className="text-sm text-red-700">
      {children}
    </p>
  );
}
