"""Menjaga migrasi tetap selaras dengan model.

Uji lain membangun tabel langsung dari metadata SQLAlchemy karena itu jauh
lebih cepat. Akibatnya migrasi tidak ikut teruji, dan model bisa berubah
tanpa migrasi yang menyertainya. Kalau itu terjadi, seluruh uji tetap hijau
sementara penempatan ke server sungguhan gagal.

Uji di berkas ini menutup celah itu.
"""

import shutil
import tempfile
from pathlib import Path

import pgserver
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

from app.model.dasar import Dasar

AKAR = Path(__file__).parent.parent


def test_migrasi_menghasilkan_skema_yang_sama_dengan_model() -> None:
    folder = Path(tempfile.mkdtemp(prefix="uji_migrasi_pg_"))
    try:
        uri = str(pgserver.get_server(folder).get_uri())
        mesin = create_engine(uri.replace("postgresql://", "postgresql+psycopg://", 1))

        from alembic import command
        from alembic.config import Config

        cfg = Config(str(AKAR / "alembic.ini"))
        cfg.set_main_option("script_location", str(AKAR / "migrasi"))
        cfg.attributes["mesin_uji"] = mesin

        import os

        os.environ["DATABASE_URL"] = str(mesin.url)
        from app.konfigurasi import ambil_pengaturan

        ambil_pengaturan.cache_clear()
        try:
            command.upgrade(cfg, "head")
        finally:
            os.environ.pop("DATABASE_URL", None)
            ambil_pengaturan.cache_clear()

        with mesin.connect() as sambungan:
            konteks = MigrationContext.configure(sambungan)
            selisih = compare_metadata(konteks, Dasar.metadata)

        mesin.dispose()
        assert selisih == [], (
            "Model dan migrasi berbeda. Jalankan:\n"
            "  uv run alembic revision --autogenerate -m '<penjelasan>'\n"
            f"Selisih yang terdeteksi: {selisih}"
        )
    finally:
        shutil.rmtree(folder, ignore_errors=True)
