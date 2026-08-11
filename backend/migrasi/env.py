"""Konfigurasi Alembic.

URL basis data TIDAK dibaca dari alembic.ini, melainkan dari
app.konfigurasi.url_basisdata(). Dengan begitu migrasi selalu memakai
basis data yang sama seperti aplikasi: PostgreSQL tersemat saat
pengembangan, DATABASE_URL saat penempatan. Satu sumber kebenaran.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app.konfigurasi import url_basisdata

# Seluruh tabel harus diimpor di sini agar terdaftar di metadata dan
# terbaca oleh --autogenerate. Tabel yang lupa diimpor akan diam-diam
# dianggap "tidak ada" lalu dihapus oleh migrasi berikutnya.
from app.model import pengguna, percobaan_masuk, token  # noqa: F401
from app.model.dasar import Dasar

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Dasar.metadata


def jalankan_luring() -> None:
    context.configure(
        url=url_basisdata(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def jalankan_daring() -> None:
    mesin = create_engine(url_basisdata())
    with mesin.connect() as sambungan:
        context.configure(connection=sambungan, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    mesin.dispose()


if context.is_offline_mode():
    jalankan_luring()
else:
    jalankan_daring()
