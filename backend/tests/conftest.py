import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pgserver
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.basisdata import ambil_sesi
from app.main import buat_aplikasi
from app.model.dasar import Dasar


@pytest.fixture(scope="session")
def mesin_uji() -> Iterator[Engine]:
    """PostgreSQL 16 sungguhan, sekali pakai, di folder sementara.

    Bukan SQLite: perbedaan perilaku NUMERIC, SELECT FOR UPDATE, dan ENUM
    justru berada di bagian yang paling ingin kita percayai (bab 10 §10.3).
    """
    folder = Path(tempfile.mkdtemp(prefix="uji_toko_pg_"))
    try:
        uri = str(pgserver.get_server(folder).get_uri())
        mesin = create_engine(uri.replace("postgresql://", "postgresql+psycopg://", 1))
        Dasar.metadata.create_all(mesin)
        yield mesin
        mesin.dispose()
    finally:
        shutil.rmtree(folder, ignore_errors=True)


@pytest.fixture
def sesi(mesin_uji: Engine) -> Iterator[Session]:
    Buat = sessionmaker(bind=mesin_uji, autoflush=False, expire_on_commit=False)
    s = Buat()
    try:
        yield s
        s.rollback()
    finally:
        for tabel in reversed(Dasar.metadata.sorted_tables):
            s.execute(tabel.delete())
        s.commit()
        s.close()


@pytest.fixture
def klien(sesi: Session) -> Iterator[TestClient]:
    aplikasi = buat_aplikasi()
    aplikasi.dependency_overrides[ambil_sesi] = lambda: sesi
    with TestClient(aplikasi) as c:
        yield c
