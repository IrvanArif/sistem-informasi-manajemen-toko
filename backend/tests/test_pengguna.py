import pytest
from sqlalchemy.orm import Session

from app.keamanan.sandi import hash_sandi, verifikasi_sandi
from app.kesalahan import KesalahanDomain, PemilikTerakhir, PeranSendiri
from app.layanan.pengguna import (
    atur_ulang_sandi,
    buat_pengguna,
    daftar_pengguna,
    ubah_pengguna,
    ubah_sandi_sendiri,
)
from app.model.pengguna import Pengguna, Peran
from app.skema.pengguna import BuatPengguna, UbahPengguna

SANDI = "rahasia123"


@pytest.fixture
def pemilik(sesi: Session) -> Pengguna:
    p = Pengguna(
        nama_pengguna="irvan",
        nama_lengkap="Irvan",
        sandi_hash=hash_sandi(SANDI),
        peran=Peran.pemilik,
    )
    sesi.add(p)
    sesi.commit()
    return p


def tambah(sesi: Session, nama: str, peran: Peran = Peran.kasir) -> Pengguna:
    return buat_pengguna(
        sesi,
        BuatPengguna(
            nama_pengguna=nama, nama_lengkap=nama.title(), sandi=SANDI, peran=peran
        ),
    )


def test_buat_akun_kasir(sesi: Session, pemilik: Pengguna) -> None:
    kasir = tambah(sesi, "kasir1")
    assert kasir.peran is Peran.kasir
    assert kasir.aktif is True
    assert kasir.sandi_hash != SANDI


def test_nama_pengguna_ganda_ditolak(sesi: Session, pemilik: Pengguna) -> None:
    with pytest.raises(KesalahanDomain) as e:
        tambah(sesi, "irvan")
    assert e.value.kode == "NAMA_PENGGUNA_TERPAKAI"


def test_menonaktifkan_pemilik_terakhir_ditolak(sesi: Session, pemilik: Pengguna) -> None:
    with pytest.raises(PemilikTerakhir):
        ubah_pengguna(sesi, pemilik.id, UbahPengguna(aktif=False), oleh=pemilik)


def test_menurunkan_peran_pemilik_terakhir_ditolak(
    sesi: Session, pemilik: Pengguna
) -> None:
    lain = tambah(sesi, "admin2", Peran.pemilik)
    lain.aktif = False
    sesi.commit()
    with pytest.raises(PemilikTerakhir):
        ubah_pengguna(sesi, pemilik.id, UbahPengguna(peran=Peran.kasir), oleh=lain)


def test_mengubah_peran_sendiri_ditolak(sesi: Session, pemilik: Pengguna) -> None:
    tambah(sesi, "admin2", Peran.pemilik)
    with pytest.raises(PeranSendiri):
        ubah_pengguna(sesi, pemilik.id, UbahPengguna(peran=Peran.kasir), oleh=pemilik)


def test_menonaktifkan_pemilik_boleh_bila_ada_pemilik_lain(
    sesi: Session, pemilik: Pengguna
) -> None:
    lain = tambah(sesi, "admin2", Peran.pemilik)
    assert ubah_pengguna(sesi, pemilik.id, UbahPengguna(aktif=False), oleh=lain).aktif is False


def test_akun_dinonaktifkan_bukan_dihapus(sesi: Session, pemilik: Pengguna) -> None:
    kasir = tambah(sesi, "kasir1")
    ubah_pengguna(sesi, kasir.id, UbahPengguna(aktif=False), oleh=pemilik)
    assert sesi.get(Pengguna, kasir.id) is not None


def test_atur_ulang_sandi(sesi: Session, pemilik: Pengguna) -> None:
    kasir = tambah(sesi, "kasir1")
    atur_ulang_sandi(sesi, kasir.id, "sandibaru456")
    sesi.refresh(kasir)
    assert verifikasi_sandi("sandibaru456", kasir.sandi_hash) is True


def test_ubah_sandi_sendiri_butuh_sandi_lama(sesi: Session, pemilik: Pengguna) -> None:
    with pytest.raises(KesalahanDomain) as e:
        ubah_sandi_sendiri(sesi, pemilik, "salah", "sandibaru456")
    assert e.value.kode == "SANDI_LAMA_SALAH"


def test_ubah_sandi_sendiri_berhasil(sesi: Session, pemilik: Pengguna) -> None:
    ubah_sandi_sendiri(sesi, pemilik, SANDI, "sandibaru456")
    sesi.refresh(pemilik)
    assert verifikasi_sandi("sandibaru456", pemilik.sandi_hash) is True


def test_daftar_pengguna_terurut(sesi: Session, pemilik: Pengguna) -> None:
    tambah(sesi, "zaki")
    tambah(sesi, "budi")
    nama = [p.nama_pengguna for p in daftar_pengguna(sesi)]
    assert nama == sorted(nama)
