import csv
import io
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from app.kesalahan import KesalahanDomain
from app.layanan.produk import buat_kategori, buat_produk, daftar_kategori
from app.model.kategori import Kategori
from app.skema.impor import BarisGagal, HasilImpor
from app.skema.produk import ProdukMasuk, SatuanMasuk

KOLOM_WAJIB = ["kode", "nama", "satuan_dasar", "harga_jual"]
KOLOM_PILIHAN = ["kategori", "barcode", "stok_awal", "stok_minimum"]

# Baris pertama berisi kepala kolom, sehingga baris data pertama adalah
# baris kedua di berkas. Nomor yang dilaporkan mengikuti nomor baris yang
# dilihat pemilik saat membuka berkasnya, bukan nomor indeks di dalam kode.
BARIS_PERTAMA_DATA = 2


def _angka(nilai: str, nama_kolom: str) -> Decimal:
    teks = (nilai or "").strip().replace(",", ".")
    if not teks:
        return Decimal("0")
    try:
        return Decimal(teks)
    except InvalidOperation as e:
        raise ValueError(f"Kolom {nama_kolom} bukan angka yang sah: {nilai!r}") from e


def _bulat(nilai: str, nama_kolom: str) -> int:
    angka = _angka(nilai, nama_kolom)
    if angka != angka.to_integral_value():
        raise ValueError(f"Kolom {nama_kolom} harus bilangan bulat rupiah: {nilai!r}")
    return int(angka)


def pemisah_kolom(isi: str) -> str:
    """Menebak pemisah kolom dari baris kepalanya.

    Lembar kerja berbahasa Indonesia mengekspor CSV dengan titik koma,
    justru karena koma sudah dipakai sebagai pemisah desimal. Memaksa
    pemilik mengubah setelan wilayah komputernya lebih dulu adalah cara
    tercepat membuat impor tidak pernah dipakai.
    """
    kepala = isi.splitlines()[0] if isi.strip() else ""
    return ";" if kepala.count(";") > kepala.count(",") else ","


def _pembaca(isi: str) -> csv.DictReader[str]:
    return csv.DictReader(io.StringIO(isi), delimiter=pemisah_kolom(isi))


def _baca_kepala(pembaca: csv.DictReader[str]) -> None:
    kolom = [k.strip().lower() for k in (pembaca.fieldnames or [])]
    kurang = [k for k in KOLOM_WAJIB if k not in kolom]
    if kurang:
        raise KesalahanDomain(
            "KOLOM_CSV_KURANG",
            "Berkas kekurangan kolom: " + ", ".join(kurang) + ". "
            "Kolom wajib: " + ", ".join(KOLOM_WAJIB) + ". "
            "Kolom pilihan: " + ", ".join(KOLOM_PILIHAN) + ".",
            detail={"kurang": kurang},
        )


def _ke_produk_masuk(baris: dict[str, str], kategori: dict[str, int]) -> ProdukMasuk:
    kode = (baris.get("kode") or "").strip()
    nama = (baris.get("nama") or "").strip()
    satuan_dasar = (baris.get("satuan_dasar") or "").strip()

    for label, nilai in (("kode", kode), ("nama", nama), ("satuan_dasar", satuan_dasar)):
        if not nilai:
            raise ValueError(f"Kolom {label} kosong")

    nama_kategori = (baris.get("kategori") or "").strip()
    barcode = (baris.get("barcode") or "").strip() or None

    return ProdukMasuk(
        kode=kode,
        nama=nama,
        kategori_id=kategori.get(nama_kategori.lower()) if nama_kategori else None,
        satuan_dasar=satuan_dasar,
        stok_minimum=_angka(baris.get("stok_minimum", ""), "stok_minimum"),
        stok_awal=_angka(baris.get("stok_awal", ""), "stok_awal"),
        satuan=[
            SatuanMasuk(
                nama=satuan_dasar,
                faktor=Decimal("1"),
                harga_jual=_bulat(baris.get("harga_jual", ""), "harga_jual"),
                barcode=barcode,
                is_dasar=True,
            )
        ],
    )


def _peta_kategori(sesi: Session) -> dict[str, int]:
    return {k.nama.lower(): k.id for k in daftar_kategori(sesi)}


def _siapkan_kategori(sesi: Session, isi: str) -> dict[str, int]:
    """Membuat kategori yang disebut CSV tetapi belum ada.

    Menolak seluruh berkas hanya karena kategorinya belum terdaftar akan
    memaksa pemilik mengetik ulang daftar kategori secara manual lebih
    dulu, padahal informasinya sudah ada di berkas itu.
    """
    ada = _peta_kategori(sesi)
    pembaca = _pembaca(isi)
    _baca_kepala(pembaca)
    baru = {
        (b.get("kategori") or "").strip()
        for b in pembaca
        if (b.get("kategori") or "").strip()
    }
    for nama in sorted(baru):
        if nama.lower() not in ada:
            k: Kategori = buat_kategori(sesi, nama)
            ada[nama.lower()] = k.id
    return ada


def periksa(sesi: Session, isi: str) -> HasilImpor:
    """Memeriksa berkas tanpa menyimpan apa pun.

    Tidak meninggalkan keadaan sementara di server. Saat dijalankan, berkas
    yang sama dikirim ulang dan diperiksa ulang dari nol, sehingga tidak
    ada token yang bisa kedaluwarsa di tengah pekerjaan (bab 07 §7.4).
    """
    pembaca = _pembaca(isi)
    _baca_kepala(pembaca)
    kategori = _peta_kategori(sesi)

    sah = 0
    gagal: list[BarisGagal] = []
    kode_terlihat: set[str] = set()

    for nomor, baris in enumerate(pembaca, start=BARIS_PERTAMA_DATA):
        try:
            data = _ke_produk_masuk(baris, kategori)
            if data.kode in kode_terlihat:
                raise ValueError(f"Kode {data.kode} muncul lebih dari sekali di berkas")
            kode_terlihat.add(data.kode)
            sah += 1
        except (ValueError, KesalahanDomain) as e:
            pesan = e.pesan if isinstance(e, KesalahanDomain) else str(e)
            gagal.append(BarisGagal(baris=nomor, alasan=pesan))

    return HasilImpor(sah=sah, gagal=gagal)


def jalankan(sesi: Session, isi: str, pengguna_id: int) -> HasilImpor:
    """Menyimpan baris yang sah, melewati yang gagal.

    Baris yang gagal tidak menghentikan sisanya. Menolak seluruh berkas
    karena tiga baris rusak dari lima ratus akan membuat pemilik
    mengulang unggahan berkali-kali tanpa kemajuan.
    """
    kategori = _siapkan_kategori(sesi, isi)
    pembaca = _pembaca(isi)
    _baca_kepala(pembaca)

    tersimpan = 0
    gagal: list[BarisGagal] = []

    for nomor, baris in enumerate(pembaca, start=BARIS_PERTAMA_DATA):
        try:
            data = _ke_produk_masuk(baris, kategori)
            buat_produk(sesi, data, pengguna_id)
            tersimpan += 1
        except (ValueError, KesalahanDomain) as e:
            sesi.rollback()
            pesan = e.pesan if isinstance(e, KesalahanDomain) else str(e)
            gagal.append(BarisGagal(baris=nomor, alasan=pesan))

    return HasilImpor(sah=tersimpan, gagal=gagal, tersimpan=tersimpan)


def contoh_csv() -> str:
    """Berkas contoh berisi kepala kolom yang benar dan dua baris teladan."""
    return (
        "kode,nama,kategori,satuan_dasar,harga_jual,barcode,stok_awal,stok_minimum\n"
        "P001,Indomie Goreng,Mi Instan,bungkus,3500,8991002101234,120,20\n"
        "P002,Beras Pandan Wangi,Sembako,kg,14000,,42.5,10\n"
    )
