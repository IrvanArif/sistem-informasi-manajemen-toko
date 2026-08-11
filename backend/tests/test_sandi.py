import pytest
from argon2.exceptions import InvalidHashError

from app.keamanan.sandi import hash_sandi, verifikasi_sandi


def test_sandi_benar_diterima() -> None:
    assert verifikasi_sandi("rahasia123", hash_sandi("rahasia123")) is True


def test_sandi_salah_ditolak() -> None:
    assert verifikasi_sandi("salah", hash_sandi("rahasia123")) is False


def test_hash_selalu_berbeda_meski_sandi_sama() -> None:
    """Argon2 menyisipkan garam acak, sehingga dua hash tak pernah sama.

    Kalau uji ini gagal, hash-nya tanpa garam dan tabel sandi bisa
    dibongkar dengan tabel pelangi.
    """
    assert hash_sandi("rahasia123") != hash_sandi("rahasia123")


def test_sandi_tidak_pernah_tampak_di_hash() -> None:
    assert "rahasia123" not in hash_sandi("rahasia123")


def test_hash_memakai_argon2id() -> None:
    assert hash_sandi("rahasia123").startswith("$argon2id$")


def test_hash_rusak_melempar_kesalahan_bukan_false() -> None:
    """Data rusak harus berisik, bukan diam-diam jadi "sandi salah"."""
    with pytest.raises(InvalidHashError):
        verifikasi_sandi("apa pun", "bukan-hash-argon2")
