import pytest
from sqlalchemy.orm import Session

from app.keamanan.sandi import verifikasi_sandi
from app.kesalahan import KesalahanDomain
from app.model.pengguna import Peran
from app.perintah.buat_pemilik import buat_pemilik_pertama


def test_membuat_pemilik_pertama(sesi: Session) -> None:
    pemilik = buat_pemilik_pertama(sesi, "irvan", "Irvan", "rahasia123")
    assert pemilik.peran is Peran.pemilik
    assert pemilik.aktif is True
    assert verifikasi_sandi("rahasia123", pemilik.sandi_hash) is True


def test_menolak_bila_sudah_ada_pengguna(sesi: Session) -> None:
    """Mencegah perintah ini dipakai membuat pintu belakang."""
    buat_pemilik_pertama(sesi, "irvan", "Irvan", "rahasia123")
    with pytest.raises(KesalahanDomain) as e:
        buat_pemilik_pertama(sesi, "orang2", "Orang Dua", "rahasia123")
    assert e.value.kode == "SUDAH_ADA_PENGGUNA"


def test_menolak_sandi_pendek(sesi: Session) -> None:
    with pytest.raises(KesalahanDomain) as e:
        buat_pemilik_pertama(sesi, "irvan", "Irvan", "pendek")
    assert e.value.kode == "SANDI_TERLALU_PENDEK"
