from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.konfigurasi import url_basisdata


@lru_cache
def ambil_mesin() -> Engine:
    """Mesin SQLAlchemy, dibuat saat pertama dibutuhkan.

    Sengaja tidak dibuat saat modul diimpor: `url_basisdata()` bisa
    menyalakan PostgreSQL tersemat, dan itu tidak boleh terjadi hanya
    karena sebuah berkas mengimpor modul ini. Uji, misalnya, memakai
    basis datanya sendiri dan tidak pernah butuh basis data pengembangan.
    """
    return create_engine(url_basisdata(), pool_pre_ping=True)


def ambil_sesi() -> Iterator[Session]:
    Buat = sessionmaker(bind=ambil_mesin(), autoflush=False, expire_on_commit=False)
    sesi = Buat()
    try:
        yield sesi
    finally:
        sesi.close()
