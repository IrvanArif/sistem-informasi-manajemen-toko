from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_pengurai = PasswordHasher()


def hash_sandi(sandi: str) -> str:
    return _pengurai.hash(sandi)


def verifikasi_sandi(sandi: str, hash_tersimpan: str) -> bool:
    """True bila sandi cocok.

    Hanya VerifyMismatchError yang ditangkap, yaitu keadaan "sandi salah"
    yang memang wajar terjadi. Hash yang rusak atau berformat asing
    melempar kesalahan lain dan sengaja dibiarkan naik: itu pertanda data
    rusak, bukan pengguna salah ketik, dan menelannya menjadi False akan
    menyembunyikannya sampai berbulan-bulan kemudian.
    """
    try:
        return _pengurai.verify(hash_tersimpan, sandi)
    except VerifyMismatchError:
        return False
