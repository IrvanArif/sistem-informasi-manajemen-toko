"""Menyalakan PostgreSQL tersemat untuk pengembangan.

Server tetap hidup setelah skrip ini selesai, dan datanya tinggal di
backend/data_pg/. Untuk memulai dari nol, hapus folder itu lalu jalankan lagi.

Tidak ada yang dipasang ke sistem: binari PostgreSQL dibawa oleh paket
`pgserver` di dalam lingkungan virtual proyek. Lihat ADR-0009.
"""

from pathlib import Path

import pgserver

DATA = Path(__file__).parent.parent / "data_pg"


def uri_basisdata_lokal() -> str:
    """URI PostgreSQL lokal. Menyalakan servernya bila belum hidup."""
    DATA.mkdir(parents=True, exist_ok=True)
    # str() bukan hiasan: pgserver tidak bertipe, sehingga tanpa ini mypy
    # ketat melihat nilai balik Any dan menolaknya.
    return str(pgserver.get_server(DATA, cleanup_mode=None).get_uri())


def uri_sqlalchemy() -> str:
    """URI yang sama, dalam bentuk yang dimengerti SQLAlchemy."""
    return uri_basisdata_lokal().replace("postgresql://", "postgresql+psycopg://", 1)


def main() -> None:
    print("PostgreSQL siap.")
    print(f"DATABASE_URL={uri_sqlalchemy()}")


if __name__ == "__main__":
    main()
