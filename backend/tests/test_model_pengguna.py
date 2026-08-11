import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.model.pengguna import Pengguna, Peran


def buat(sesi: Session, nama: str, peran: Peran = Peran.kasir) -> Pengguna:
    p = Pengguna(
        nama_pengguna=nama, nama_lengkap=nama.title(), sandi_hash="x", peran=peran
    )
    sesi.add(p)
    sesi.commit()
    return p


def test_nama_pengguna_wajib_unik(sesi: Session) -> None:
    buat(sesi, "irvan")
    sesi.add(
        Pengguna(
            nama_pengguna="irvan",
            nama_lengkap="Irvan Lain",
            sandi_hash="y",
            peran=Peran.pemilik,
        )
    )
    with pytest.raises(IntegrityError):
        sesi.commit()


def test_pengguna_baru_aktif_secara_bawaan(sesi: Session) -> None:
    assert buat(sesi, "kasir1").aktif is True


def test_peran_tersimpan_sebagai_enum(sesi: Session) -> None:
    p = buat(sesi, "pemilik1", Peran.pemilik)
    sesi.refresh(p)
    assert p.peran is Peran.pemilik


def test_kolom_waktu_terisi_sendiri(sesi: Session) -> None:
    p = buat(sesi, "kasir2")
    sesi.refresh(p)
    assert p.dibuat_pada is not None
    assert p.diubah_pada is not None


def test_menonaktifkan_bukan_menghapus(sesi: Session) -> None:
    p = buat(sesi, "kasir3")
    p.aktif = False
    sesi.commit()
    assert sesi.get(Pengguna, p.id) is not None
