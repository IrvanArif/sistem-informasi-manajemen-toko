import { useEffect, useState } from "react";
import type { SesiKas } from "../../api/domain";
import { rupiah } from "../../api/domain";
import { KesalahanApi, minta } from "../../api/klien";
import { Kolom, PesanKesalahan, Tombol } from "../../komponen/dasar";

function pesanDari(e: unknown): string {
  return e instanceof KesalahanApi ? e.pesan : "Tidak bisa terhubung ke server";
}

export function BukaSesiKas({ onDibuka }: { onDibuka: () => void }) {
  const [modal, setModal] = useState("0");
  const [kesalahan, setKesalahan] = useState<string | null>(null);
  const [sibuk, setSibuk] = useState(false);

  async function buka() {
    setSibuk(true);
    setKesalahan(null);
    try {
      await minta("/sesi-kas", {
        metode: "POST",
        muatan: { modal_awal: Number(modal.replace(/\D/g, "")) || 0 },
      });
      onDibuka();
    } catch (e) {
      setKesalahan(pesanDari(e));
    } finally {
      setSibuk(false);
    }
  }

  return (
    <section className="p-4 max-w-sm mx-auto space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">Buka sesi kas</h1>
      <p className="text-gray-700">
        Isi uang yang ada di laci sekarang. Tanpa ini, kas fisik tidak bisa
        dicocokkan saat tutup kasir nanti.
      </p>
      <Kolom
        label="Modal awal laci"
        autoFocus
        inputMode="numeric"
        value={modal}
        onChange={(e) => setModal(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && void buka()}
      />
      <PesanKesalahan>{kesalahan}</PesanKesalahan>
      <Tombol utama className="w-full" disabled={sibuk} onClick={() => void buka()}>
        {sibuk ? "Membuka..." : "Mulai melayani"}
      </Tombol>
    </section>
  );
}

export function TutupSesiKas({
  sesi,
  onDitutup,
  onBatal,
}: {
  sesi: SesiKas;
  onDitutup: () => void;
  onBatal: () => void;
}) {
  const [sistem, setSistem] = useState<number | null>(null);
  const [fisik, setFisik] = useState("");
  const [catatan, setCatatan] = useState("");
  const [kesalahan, setKesalahan] = useState<string | null>(null);
  const [sibuk, setSibuk] = useState(false);

  useEffect(() => {
    void minta<{ kas_sistem: number }>(`/sesi-kas/${sesi.id}/kas-sistem`)
      .then((d) => setSistem(d.kas_sistem))
      .catch(() => setSistem(null));
  }, [sesi.id]);

  const angkaFisik = Number(fisik.replace(/\D/g, "")) || 0;
  const selisih = sistem === null ? 0 : angkaFisik - sistem;

  async function tutup() {
    setSibuk(true);
    setKesalahan(null);
    try {
      await minta(`/sesi-kas/${sesi.id}/tutup`, {
        metode: "POST",
        muatan: { kas_fisik: angkaFisik, catatan: catatan || null },
      });
      onDitutup();
    } catch (e) {
      setKesalahan(pesanDari(e));
    } finally {
      setSibuk(false);
    }
  }

  return (
    <section className="p-4 max-w-sm mx-auto space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">Tutup kasir</h1>

      <div className="rounded border border-gray-300 p-3">
        <p className="text-sm text-gray-700">Menurut sistem, di laci seharusnya ada</p>
        <p className="text-2xl font-bold text-gray-900">
          {sistem === null ? "..." : rupiah(sistem)}
        </p>
        <p className="mt-1 text-sm text-gray-700">
          modal awal {rupiah(sesi.modal_awal)} ditambah penjualan tunai
        </p>
      </div>

      <Kolom
        label="Hitung uang di laci sekarang"
        autoFocus
        inputMode="numeric"
        value={fisik}
        onChange={(e) => setFisik(e.target.value)}
      />

      {fisik !== "" && sistem !== null && (
        <p className={selisih === 0 ? "text-gray-900" : "font-medium text-amber-700"}>
          Selisih {rupiah(selisih)}
          {selisih !== 0 && " · wajib diisi catatan"}
        </p>
      )}

      {selisih !== 0 && fisik !== "" && (
        <Kolom
          label="Catatan selisih"
          value={catatan}
          onChange={(e) => setCatatan(e.target.value)}
          placeholder="mis. uang kembalian kurang dihitung"
        />
      )}

      <PesanKesalahan>{kesalahan}</PesanKesalahan>

      <div className="flex gap-2">
        <Tombol utama className="flex-1" disabled={sibuk || fisik === ""}
                onClick={() => void tutup()}>
          {sibuk ? "Menutup..." : "Tutup kasir"}
        </Tombol>
        <Tombol onClick={onBatal}>Batal</Tombol>
      </div>
    </section>
  );
}
