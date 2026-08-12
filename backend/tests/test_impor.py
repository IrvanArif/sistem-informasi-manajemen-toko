from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.keamanan.sandi import hash_sandi
from app.keamanan.token import terbitkan_token_akses
from app.kesalahan import KesalahanDomain
from app.layanan.impor import contoh_csv, jalankan, periksa
from app.layanan.produk import cari_produk
from app.layanan.stok import kartu_stok, periksa_keselarasan
from app.model.pengguna import Pengguna, Peran

KEPALA = "kode,nama,kategori,satuan_dasar,harga_jual,barcode,stok_awal,stok_minimum\n"


@pytest.fixture
def pemilik(sesi: Session) -> Pengguna:
    p = Pengguna(nama_pengguna="irvan", nama_lengkap="Irvan",
                 sandi_hash=hash_sandi("rahasia123"), peran=Peran.pemilik)
    sesi.add(p)
    sesi.commit()
    return p


def test_berkas_contoh_lolos_pemeriksaan_sendiri(sesi: Session) -> None:
    """Contoh yang diberikan ke pemilik harus benar-benar bisa diimpor."""
    hasil = periksa(sesi, contoh_csv())
    assert hasil.gagal == []
    assert hasil.sah == 2


def test_impor_menyimpan_produk_dan_stok_awal(
    sesi: Session, pemilik: Pengguna
) -> None:
    hasil = jalankan(sesi, contoh_csv(), pemilik.id)
    assert hasil.tersimpan == 2

    produk = {p.kode: p for p in cari_produk(sesi, "")}
    assert produk["P001"].stok == Decimal("120.000")
    assert produk["P002"].stok == Decimal("42.500")  # barang curah, berdesimal
    assert kartu_stok(sesi, produk["P001"].id)[0].tipe.value == "stok_awal"
    assert periksa_keselarasan(sesi) == []


def test_kategori_dibuat_sendiri_dari_berkas(
    sesi: Session, pemilik: Pengguna
) -> None:
    """Menolak berkas karena kategorinya belum ada akan memaksa pemilik
    mengetik ulang daftar kategori, padahal sudah tertulis di berkas."""
    jalankan(sesi, contoh_csv(), pemilik.id)
    produk = {p.kode: p for p in cari_produk(sesi, "")}
    assert produk["P001"].kategori_id is not None
    assert produk["P001"].kategori_id != produk["P002"].kategori_id


def test_kolom_wajib_kurang_ditolak_dengan_daftar_kolomnya(sesi: Session) -> None:
    with pytest.raises(KesalahanDomain) as e:
        periksa(sesi, "kode,nama\nP001,Indomie\n")
    assert e.value.kode == "KOLOM_CSV_KURANG"
    assert "satuan_dasar" in e.value.pesan
    assert "harga_jual" in e.value.pesan


def test_baris_rusak_menyebut_nomor_baris_yang_benar(sesi: Session) -> None:
    """Nomor mengikuti yang dilihat pemilik saat membuka berkasnya."""
    isi = (
        KEPALA
        + "P001,Indomie,Mi,bungkus,3500,,10,2\n"      # baris 2, sah
        + "P002,,Mi,bungkus,3000,,5,1\n"              # baris 3, nama kosong
        + "P003,Beras,Sembako,kg,bukanangka,,5,1\n"   # baris 4, harga bukan angka
        + "P004,Gula,Sembako,kg,12000,,5,1\n"         # baris 5, sah
    )
    hasil = periksa(sesi, isi)
    assert hasil.sah == 2
    assert [g.baris for g in hasil.gagal] == [3, 4]
    assert "nama" in hasil.gagal[0].alasan
    assert "harga_jual" in hasil.gagal[1].alasan


def test_kode_ganda_di_dalam_berkas_terdeteksi(sesi: Session) -> None:
    isi = KEPALA + "P001,A,,pcs,1000,,0,0\n" + "P001,B,,pcs,2000,,0,0\n"
    hasil = periksa(sesi, isi)
    assert hasil.sah == 1
    assert hasil.gagal[0].baris == 3
    assert "lebih dari sekali" in hasil.gagal[0].alasan


def test_baris_gagal_tidak_menghentikan_yang_lain(
    sesi: Session, pemilik: Pengguna
) -> None:
    """Tiga baris rusak dari lima ratus tidak boleh membatalkan semuanya."""
    isi = (
        KEPALA
        + "P001,Indomie,Mi,bungkus,3500,,10,2\n"
        + "P002,,Mi,bungkus,3000,,5,1\n"
        + "P003,Gula,Sembako,kg,12000,,5,1\n"
    )
    hasil = jalankan(sesi, isi, pemilik.id)
    assert hasil.tersimpan == 2
    assert [g.baris for g in hasil.gagal] == [3]
    assert {p.kode for p in cari_produk(sesi, "")} == {"P001", "P003"}


def test_pratinjau_tidak_menyimpan_apa_pun(sesi: Session) -> None:
    periksa(sesi, contoh_csv())
    assert cari_produk(sesi, "") == []


def test_koma_diterima_sebagai_pemisah_desimal(
    sesi: Session, pemilik: Pengguna
) -> None:
    """Lembar kerja berbahasa Indonesia menulis 42,5 bukan 42.5.

    Menolaknya berarti menyalahkan pemilik atas setelan wilayah
    komputernya sendiri.
    """
    # Berpemisah titik koma, seperti ekspor lembar kerja berbahasa Indonesia
    isi = (
        "kode;nama;kategori;satuan_dasar;harga_jual;barcode;stok_awal;stok_minimum\n"
        "P001;Beras;Sembako;kg;14000;;42,5;10\n"
    )
    jalankan(sesi, isi, pemilik.id)
    assert cari_produk(sesi, "P001")[0].stok == Decimal("42.500")


def kepala_pemilik(p: Pengguna) -> dict[str, str]:
    return {"Authorization": f"Bearer {terbitkan_token_akses(p.id, p.peran.value)}"}


def test_jalur_impor_tidak_tertangkap_jalur_produk_id(
    klien: TestClient, pemilik: Pengguna
) -> None:
    """/produk/impor/contoh tidak boleh dibaca sebagai /produk/{produk_id}.

    Bila urutan pendaftaran rutenya salah, "impor" akan dicoba diuraikan
    sebagai angka dan permintaannya ditolak 422 tanpa sebab yang jelas.
    """
    j = klien.get("/api/v1/produk/impor/contoh", headers=kepala_pemilik(pemilik))
    assert j.status_code == 200
    assert j.text.startswith("kode,nama,kategori")


def test_impor_lewat_api(klien: TestClient, pemilik: Pengguna) -> None:
    berkas = {"berkas": ("produk.csv", contoh_csv(), "text/csv")}
    pratinjau = klien.post("/api/v1/produk/impor/pratinjau", files=berkas,
                           headers=kepala_pemilik(pemilik))
    assert pratinjau.status_code == 200
    assert pratinjau.json() == {"sah": 2, "gagal": [], "tersimpan": 0}

    jalan = klien.post("/api/v1/produk/impor/jalankan", files=berkas,
                       headers=kepala_pemilik(pemilik))
    assert jalan.json()["tersimpan"] == 2


def test_impor_hanya_untuk_pemilik(klien: TestClient, sesi: Session) -> None:
    kasir = Pengguna(nama_pengguna="kasir1", nama_lengkap="Kasir",
                     sandi_hash=hash_sandi("rahasia123"), peran=Peran.kasir)
    sesi.add(kasir)
    sesi.commit()
    j = klien.post("/api/v1/produk/impor/jalankan",
                   files={"berkas": ("p.csv", contoh_csv(), "text/csv")},
                   headers=kepala_pemilik(kasir))
    assert j.status_code == 403
