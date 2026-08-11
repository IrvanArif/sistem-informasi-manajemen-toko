"""Membuat akun pemilik pertama.

Tanpa perintah ini sistem yang baru dipasang tidak punya siapa pun yang
bisa masuk, sementara endpoint pembuatan akun menuntut pemilik yang sudah
masuk. Perintah ini memutus lingkaran itu, dan sengaja menolak berjalan
begitu sudah ada pengguna, supaya tidak bisa dipakai membuat pintu
belakang di sistem yang sudah beroperasi.
"""

import sys

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.basisdata import BuatSesi
from app.keamanan.sandi import hash_sandi
from app.kesalahan import KesalahanDomain
from app.model.pengguna import Pengguna, Peran

PANJANG_SANDI_MINIMUM = 8


def buat_pemilik_pertama(
    sesi: Session, nama_pengguna: str, nama_lengkap: str, sandi: str
) -> Pengguna:
    jumlah = int(sesi.execute(select(func.count()).select_from(Pengguna)).scalar_one())
    if jumlah > 0:
        raise KesalahanDomain(
            "SUDAH_ADA_PENGGUNA",
            "Sistem sudah punya pengguna. Buat akun baru lewat menu Pengaturan.",
        )
    if len(sandi) < PANJANG_SANDI_MINIMUM:
        raise KesalahanDomain(
            "SANDI_TERLALU_PENDEK",
            f"Sandi minimal {PANJANG_SANDI_MINIMUM} karakter",
        )

    pemilik = Pengguna(
        nama_pengguna=nama_pengguna,
        nama_lengkap=nama_lengkap,
        sandi_hash=hash_sandi(sandi),
        peran=Peran.pemilik,
    )
    sesi.add(pemilik)
    sesi.commit()
    return pemilik


def main() -> None:
    if len(sys.argv) != 4:
        print(
            "Pemakaian: python -m app.perintah.buat_pemilik "
            "<nama_pengguna> <nama_lengkap> <sandi>"
        )
        raise SystemExit(1)
    with BuatSesi() as sesi:
        try:
            pemilik = buat_pemilik_pertama(sesi, sys.argv[1], sys.argv[2], sys.argv[3])
        except KesalahanDomain as e:
            # Pesannya sudah ditulis untuk dibaca manusia. Menampilkannya
            # apa adanya jauh lebih berguna daripada menumpahkan traceback.
            print(f"Gagal: {e.pesan}", file=sys.stderr)
            raise SystemExit(1) from None
        print(f"Pemilik dibuat: {pemilik.nama_pengguna}")


if __name__ == "__main__":
    main()
