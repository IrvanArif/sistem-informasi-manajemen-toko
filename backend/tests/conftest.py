import os

# Disetel SEBELUM modul aplikasi diimpor, karena Pengaturan dibaca saat
# impor dan RAHASIA_JWT wajib ada. Tanpa ini, uji hanya berjalan di mesin
# yang kebetulan punya backend/.env, dan berkas itu tidak ikut ter-commit.
# Nilai di bawah khusus uji dan tidak pernah dipakai di mana pun.
os.environ.setdefault("RAHASIA_JWT", "rahasia-khusus-uji-jangan-dipakai-di-mana-pun")
os.environ.setdefault("LINGKUNGAN", "pengembangan")

import shutil  # noqa: E402
import tempfile  # noqa: E402
from collections.abc import Iterator  # noqa: E402
from pathlib import Path  # noqa: E402

import pgserver  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import Engine, create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

# Mengimpor app.model mendaftarkan SELURUH tabel di metadata.
import app.model  # noqa: E402, F401
from app.basisdata import ambil_sesi  # noqa: E402
from app.main import buat_aplikasi  # noqa: E402
from app.model.dasar import Dasar  # noqa: E402


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
