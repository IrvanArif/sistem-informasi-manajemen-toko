from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.basisdata import ambil_sesi
from app.keamanan.token import TokenTidakSah, baca_token_akses
from app.kesalahan import BelumMasuk, SesiHabis, TidakBerhak
from app.model.pengguna import Pengguna, Peran


def pengguna_berjalan(
    authorization: str = Header(default=""),
    sesi: Session = Depends(ambil_sesi),
) -> Pengguna:
    """Pengguna pemilik token, dibaca ulang dari basis data.

    Perannya sengaja tidak diambil dari isi token. Token bisa saja
    diterbitkan sebelum peran penggunanya diturunkan atau akunnya
    dinonaktifkan, dan token itu masih berlaku sampai kedaluwarsa.
    Membaca ulang membuat pencabutan hak berlaku seketika.
    """
    if not authorization.startswith("Bearer "):
        raise BelumMasuk
    try:
        isi = baca_token_akses(authorization.removeprefix("Bearer "))
    except TokenTidakSah as e:
        raise SesiHabis from e

    pengguna = sesi.get(Pengguna, isi.pengguna_id)
    if pengguna is None or not pengguna.aktif:
        raise SesiHabis
    return pengguna


def wajib_pemilik(pengguna: Pengguna = Depends(pengguna_berjalan)) -> Pengguna:
    if pengguna.peran is not Peran.pemilik:
        raise TidakBerhak
    return pengguna
