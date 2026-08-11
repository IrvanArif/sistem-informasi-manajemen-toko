const DASAR = import.meta.env.VITE_API_DASAR ?? "http://localhost:8000/api/v1";

const KUNCI_AKSES = "toko.token_akses";
const KUNCI_SEGAR = "toko.token_segar";

/** Kesalahan yang datang dari server, sudah membawa pesan berbahasa Indonesia.
 *
 * Ruasnya ditulis satu per satu, bukan lewat properti parameter, karena
 * cetakan Vite menyalakan erasableSyntaxOnly: hanya sintaks yang bisa
 * dihapus begitu saja saat dikompilasi yang diizinkan.
 */
export class KesalahanApi extends Error {
  readonly kode: string;
  readonly pesan: string;
  readonly status: number;

  constructor(kode: string, pesan: string, status: number) {
    super(pesan);
    this.name = "KesalahanApi";
    this.kode = kode;
    this.pesan = pesan;
    this.status = status;
  }
}

export function simpanToken(akses: string, segar: string): void {
  localStorage.setItem(KUNCI_AKSES, akses);
  localStorage.setItem(KUNCI_SEGAR, segar);
}

export function hapusToken(): void {
  localStorage.removeItem(KUNCI_AKSES);
  localStorage.removeItem(KUNCI_SEGAR);
}

export function ambilTokenAkses(): string | null {
  return localStorage.getItem(KUNCI_AKSES);
}

export function ambilTokenSegar(): string | null {
  return localStorage.getItem(KUNCI_SEGAR);
}

export function sudahMasuk(): boolean {
  return ambilTokenAkses() !== null;
}

interface OpsiMinta {
  metode?: "GET" | "POST" | "PATCH";
  muatan?: unknown;
}

async function kirim(jalur: string, opsi: OpsiMinta): Promise<Response> {
  const token = ambilTokenAkses();
  return fetch(`${DASAR}${jalur}`, {
    method: opsi.metode ?? "GET",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: opsi.muatan === undefined ? undefined : JSON.stringify(opsi.muatan),
  });
}

/** Menukar token segar dengan pasangan baru. Mengembalikan true bila berhasil. */
async function segarkanToken(): Promise<boolean> {
  const segar = ambilTokenSegar();
  if (!segar) return false;

  const jawaban = await fetch(`${DASAR}/auth/segarkan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token_segar: segar }),
  });
  if (!jawaban.ok) {
    hapusToken();
    return false;
  }
  const isi = (await jawaban.json()) as { token_akses: string; token_segar: string };
  simpanToken(isi.token_akses, isi.token_segar);
  return true;
}

export async function minta<T>(jalur: string, opsi: OpsiMinta = {}): Promise<T> {
  let jawaban = await kirim(jalur, opsi);

  // Token akses hanya berumur 15 menit. Saat habis, ditukar sekali lalu
  // permintaannya diulang, sehingga pengguna tidak terlempar ke layar
  // masuk di tengah pekerjaan. Hanya sekali: kalau penukaran juga gagal,
  // sesinya memang sudah berakhir.
  if (jawaban.status === 401 && !jalur.startsWith("/auth/")) {
    if (await segarkanToken()) {
      jawaban = await kirim(jalur, opsi);
    }
  }

  if (jawaban.status === 204) return undefined as T;

  if (!jawaban.ok) {
    const isi = (await jawaban.json().catch(() => null)) as
      | { kode?: string; pesan?: string }
      | null;
    throw new KesalahanApi(
      isi?.kode ?? "KESALAHAN_TIDAK_DIKENAL",
      // Pesan dari server ditampilkan apa adanya. Ia sudah berbahasa
      // Indonesia dan menyebut langkah berikutnya (bab 07 §7.1).
      isi?.pesan ?? "Terjadi kesalahan sistem. Coba lagi sebentar lagi.",
      jawaban.status,
    );
  }
  return (await jawaban.json()) as T;
}
