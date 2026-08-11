import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt

from app.konfigurasi import ambil_pengaturan


class TokenTidakSah(Exception):
    """Token tidak bisa dibaca, kedaluwarsa, atau tanda tangannya salah."""


@dataclass(frozen=True)
class IsiToken:
    pengguna_id: int
    peran: str


def terbitkan_token_akses(pengguna_id: int, peran: str) -> str:
    p = ambil_pengaturan()
    sekarang = datetime.now(UTC)
    muatan = {
        "sub": str(pengguna_id),
        "peran": peran,
        "iat": sekarang,
        "exp": sekarang + timedelta(minutes=p.umur_token_akses_menit),
    }
    return jwt.encode(muatan, p.rahasia_jwt, algorithm="HS256")


def baca_token_akses(token: str) -> IsiToken:
    """Membaca isi token. Melempar TokenTidakSah bila tidak bisa dipercaya.

    Peran yang terbaca di sini hanya petunjuk. Yang menentukan hak akses
    tetap peran di basis data, karena token bisa saja diterbitkan sebelum
    peran penggunanya diturunkan.
    """
    try:
        muatan = jwt.decode(token, ambil_pengaturan().rahasia_jwt, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise TokenTidakSah(str(e)) from e
    return IsiToken(pengguna_id=int(muatan["sub"]), peran=str(muatan["peran"]))


def buat_token_segar() -> tuple[str, str]:
    """Menghasilkan (token_mentah, token_hash). Hanya hash yang disimpan."""
    mentah = secrets.token_urlsafe(48)
    return mentah, hash_token_segar(mentah)


def hash_token_segar(mentah: str) -> str:
    return hashlib.sha256(mentah.encode()).hexdigest()
