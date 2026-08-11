# Rencana Implementasi M0: Fondasi

**Tujuan:** Aplikasi kosong yang berjalan di `localhost`, tempat pemilik bisa masuk dan membuat akun kasir, dengan alur CI yang hijau.

> **Keputusan 2026-08-08: localhost dulu, penempatan menyusul.** M0 semula berakhir dengan menempatkan aplikasi ke internet. Atas permintaan pemilik proyek, seluruh M0 dikerjakan di komputer sendiri agar pengembangannya lebih ringan, dan penempatan dipindah ke [Tugas Tertunda](#tugas-tertunda-penempatan-ke-lapisan-gratis) di akhir dokumen.
>
> Konsekuensi yang diterima: kebutuhan "pemilik memantau dari HP di mana saja" belum terpenuhi sampai penempatan dikerjakan. Selama itu sistem hanya bisa dibuka dari komputer tempat ia dijalankan.
>
> Ongkos yang perlu diingat: menempatkan aplikasi kosong jauh lebih mudah dicari tahu penyebabnya saat gagal daripada menempatkan aplikasi yang sudah berisi kasir, stok, dan sinkronisasi. Semakin lama ditunda, semakin mahal.

**Arsitektur:** Backend Python (FastAPI + SQLAlchemy + Alembic) memegang seluruh aturan; frontend React SPA memegang seluruh tampilan; kontrak tipe dibangkitkan dari OpenAPI. M0 hanya membangun lapisan akses: pengguna, sandi, token, peran. Belum ada produk, belum ada transaksi.

**Perkakas:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, `uv`, PostgreSQL 16 lewat `pgserver`, Argon2, React 19, TypeScript, Vite, Tailwind, pytest, Vitest.

> **Tanpa pemasangan ke sistem.** Atas syarat pemilik proyek, tidak ada perangkat lunak yang dipasang ke laptop selain `uv` dan Node (keduanya ke folder rumah, tanpa `sudo`). PostgreSQL berjalan dari dalam lingkungan Python proyek lewat `pgserver`. Alasan lengkap dan hasil verifikasinya di [ADR-0009](../adr/0009-postgresql-tersemat-tanpa-docker.md).

**Acuan:** [Spesifikasi induk](../spesifikasi.md) · [02 Arsitektur](../perancangan/02-arsitektur.md) · [03 Model Data](../perancangan/03-model-data.md) · [07 Kontrak API](../perancangan/07-kontrak-api.md) · [08 Keamanan dan Peran](../perancangan/08-keamanan-dan-peran.md) · [09 Penanganan Error](../perancangan/09-penanganan-error.md) · [10 Strategi Pengujian](../perancangan/10-strategi-pengujian.md)

## Batasan Global

Berlaku untuk **setiap** tugas di bawah tanpa perlu diulang.

| # | Batasan | Sumber |
|---|---|---|
| G1 | **Nol biaya.** Seluruh perkakas dan layanan wajib gratis atau open source. Tidak boleh ada langganan, tidak boleh ada tagihan, tidak boleh ada layanan yang menuntut pembayaran untuk dipakai. Bila sebuah layanan meminta kartu, hentikan dan laporkan sebelum melanjutkan. | [ADR-0007](../adr/0007-lapisan-gratis-dan-portabilitas.md) |
| G2 | **Tanpa kunci penyedia.** Dilarang memakai fungsi khusus vendor. Penempatan lewat `Dockerfile` yang dibangun di sisi penyedia; Docker tidak perlu ada di laptop. | [ADR-0007](../adr/0007-lapisan-gratis-dan-portabilitas.md), [ADR-0009](../adr/0009-postgresql-tersemat-tanpa-docker.md) |
| G10 | **Tanpa pemasangan ke sistem.** Seluruh perkakas berada di folder rumah atau folder proyek. Tidak ada `sudo`, tidak ada layanan latar. | [ADR-0009](../adr/0009-postgresql-tersemat-tanpa-docker.md) |
| G3 | **Istilah domain berbahasa Indonesia** di nama tabel, kolom, fungsi layanan, endpoint, dan berkas. Kata kunci bahasa pemrograman dan nama pustaka tetap bahasa aslinya. | [ADR-0008](../adr/0008-istilah-domain-bahasa-indonesia.md) |
| G4 | **Uang selalu `BIGINT` rupiah bulat.** Jumlah barang selalu `NUMERIC(14,3)` dan `Decimal`, tidak pernah `float`. Satu-satunya pengecualian: HPP `NUMERIC(14,4)`. Belum terpakai di M0, tetapi berlaku sejak migrasi pertama. | [03 §3.4](../perancangan/03-model-data.md) |
| G5 | **Data tidak dihapus.** Pengguna dinonaktifkan lewat kolom `aktif`. Tidak ada endpoint `DELETE` di seluruh sistem. | [03 §3.3](../perancangan/03-model-data.md) |
| G6 | **`rute/` tanpa aturan bisnis.** Rute menerima permintaan, memanggil `layanan/`, mengembalikan jawaban. `layanan/` tidak tahu apa pun soal HTTP. | [02 §2.3](../perancangan/02-arsitektur.md) |
| G7 | **Uji ditulis menyusul, wajib ada sebelum digabung.** Tiap tugas berakhir dengan uji yang lulus. Dilarang menggabungkan perubahan di `backend/app/layanan/` tanpa uji. | [10 §10.2](../perancangan/10-strategi-pengujian.md) |
| G8 | **Pesan kesalahan berbahasa Indonesia** sejak dari server, memakai bentuk `{kode, pesan, detail}`. | [07 §7.1](../perancangan/07-kontrak-api.md) |
| G9 | **Rahasia lewat variabel lingkungan.** `.env` tidak pernah masuk repositori. | [08 §8.4](../perancangan/08-keamanan-dan-peran.md) |

## Berkas yang dibangun di M0

```
backend/
  pyproject.toml                 dependensi, dikelola uv
  alembic.ini
  migrasi/
    env.py
    versions/                    berkas migrasi
  app/
    main.py                      titik masuk, pemasangan rute & handler
    konfigurasi.py               pembacaan environment
    basisdata.py                 mesin & sesi SQLAlchemy
    kesalahan.py                 kelas kesalahan domain + bentuk jawaban
    model/
      __init__.py
      dasar.py                   DeclarativeBase + kolom waktu bersama
      pengguna.py                tabel pengguna
      token.py                   tabel token_segar
    skema/
      auth.py                    bentuk masuk, token, pengguna
      pengguna.py                bentuk buat & ubah pengguna
    layanan/
      pengguna.py                ATURAN BISNIS pengguna & penjagaannya
      otentikasi.py              ATURAN BISNIS masuk, token, pembatasan
    keamanan/
      sandi.py                   hash & verifikasi Argon2
      token.py                   terbitkan & baca JWT
      hak_akses.py               dependensi peran
    rute/
      auth.py
      pengguna.py
      sehat.py
  tests/
    conftest.py                  basis data uji sekali pakai
    test_sandi.py
    test_token.py
    test_otentikasi.py
    test_pengguna.py
    test_hak_akses.py

frontend/
  package.json
  vite.config.ts
  tsconfig.json
  tailwind.config.js
  index.html
  src/
    main.tsx
    App.tsx
    api/
      klien.ts                   pembungkus fetch + penyisipan token
      tipe.ts                    DIBANGKITKAN dari OpenAPI, jangan disunting
    fitur/
      masuk/LayarMasuk.tsx
      pengguna/LayarPengguna.tsx
    komponen/
      Tombol.tsx
      Kolom.tsx
      PesanKesalahan.tsx
  tests/
    klien.test.ts

backend/data_pg/                 data PostgreSQL lokal (diabaikan git)
.env.contoh                      contoh variabel, tanpa nilai rahasia
.github/workflows/uji.yml        alur CI
```

---

## Tugas 1: Perkakas lokal dan akun yang benar-benar dibutuhkan

**Tugas manusia, bukan tugas kode.**

Karena M0 dikerjakan di localhost, satu-satunya akun yang dibutuhkan adalah **GitHub**, itu pun hanya untuk alur CI di Tugas 17. Neon dan Render tidak diperlukan sampai penempatan dikerjakan.

- [x] **Langkah 1: Akun**

| Layanan | Status | Dibutuhkan untuk |
|---|---|---|
| GitHub | sudah ada | Repositori dan CI (Tugas 17) |
| Cloudflare | sudah ada | Belum terpakai; nanti untuk tampilan statis |
| Neon | **tidak didaftarkan** | Ditunda sampai penempatan |
| Render | **tidak didaftarkan** | Ditunda sampai penempatan |

Aturan yang tetap berlaku saat nanti mendaftar: **berhenti seketika bila diminta kartu kredit, kartu debit, atau data pembayaran apa pun** (G1).

- [ ] **Langkah 2: Pasang perkakas lokal**

Keduanya memasang ke folder rumah, **tanpa `sudo`**, dan tidak menyentuh sistem:

```bash
# uv, pemasang dependensi Python
curl -LsSf https://astral.sh/uv/install.sh | sh

# Node 22 lewat nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
export NVM_DIR="$HOME/.nvm" &&. "$NVM_DIR/nvm.sh" && nvm install 22
```

**Tidak ada Docker, tidak ada PostgreSQL sistem, tidak ada `sudo`.** PostgreSQL datang sebagai dependensi Python di Tugas 2 ([ADR-0009](../adr/0009-postgresql-tersemat-tanpa-docker.md)).

- [ ] **Langkah 3: Pastikan semuanya terbaca**

```bash
uv --version && node --version && npm --version
```

Diharapkan: tiga versi tercetak. Bila `node` tidak ditemukan di terminal baru, jalankan `. "$HOME/.nvm/nvm.sh"` lebih dulu.

---

## Tugas 2: Kerangka repositori dan PostgreSQL lokal

**Berkas:**
- Buat: `backend/pyproject.toml`, `backend/skrip/nyalakan_basisdata.py`, `backend/.env.contoh`, `backend/app/__init__.py`
- Modifikasi: `.gitignore`

**Antarmuka:**
- Menghasilkan: PostgreSQL 16 berjalan dari `backend/data_pg/`, dijangkau lewat soket Unix; fungsi `uri_basisdata_lokal() -> str`.

- [ ] **Langkah 1: Tulis `backend/pyproject.toml`**

```toml
[project]
name = "toko-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "sqlalchemy>=2.0.36",
    "alembic>=1.14",
    "psycopg[binary]>=3.2",
    "pydantic>=2.10",
    "pydantic-settings>=2.6",
    "argon2-cffi>=23.1",
    "pyjwt>=2.10",
    "structlog>=24.4",
    "pgserver>=0.1.4",
]

[dependency-groups]
dev = [
    "pytest>=8.3",
    "httpx2>=2.10",   # TestClient starlette menganggap httpx lama usang
    "hypothesis>=6.122",
    "ruff>=0.8",
    "mypy>=1.13",
    "pip-audit>=2.7",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
# Ditulis tegas, bukan mengandalkan bawaan ruff, supaya pembaruan ruff
# tidak diam-diam mengubah aturan yang berlaku di proyek ini.
select = ["E", "F", "I", "B", "UP", "SIM"]

[tool.ruff.lint.flake8-bugbear]
# Depends() memang dipanggil di nilai bawaan argumen. Itu cara baku
# FastAPI, bukan jebakan nilai bawaan yang dapat berubah.
extend-immutable-calls = [
    "fastapi.Depends", "fastapi.Query", "fastapi.Header",
    "fastapi.Path", "fastapi.Body", "fastapi.Form", "fastapi.File",
]

[tool.mypy]
python_version = "3.12"
strict = true

# pgserver tidak menyertakan informasi tipe (tanpa py.typed), sehingga mypy
# ketat menolak setiap atributnya. Dilonggarkan hanya untuk paket ini.
[[tool.mypy.overrides]]
module = ["pgserver", "pgserver.*"]
ignore_missing_imports = true
follow_imports = "skip"

[tool.pytest.ini_options]
testpaths = ["tests"]
# Tanpa ini, pytest tidak menemukan paket `app` dan `skrip`, karena proyek
# ini dijalankan langsung dari sumbernya dan tidak dipasang sebagai paket.
pythonpath = ["."]
```

- [ ] **Langkah 2: Tulis `backend/skrip/nyalakan_basisdata.py`**

```python
"""Menyalakan PostgreSQL tersemat untuk pengembangan.

Server tetap hidup setelah skrip ini selesai, dan datanya tinggal di
backend/data_pg/. Untuk memulai dari nol, hentikan lalu hapus foldernya.
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
```

`cleanup_mode=None` penting: tanpanya server ikut mati saat skrip selesai, dan aplikasi tidak akan menemukan apa pun untuk disambungi.

- [ ] **Langkah 3: Tulis `backend/.env.contoh` dan perbarui `.gitignore`**

Ditaruh di `backend/`, bukan di akar repositori, karena `env_file=".env"` dibaca
relatif terhadap tempat aplikasi dijalankan.

```bash
# backend/.env.contoh
# Salin menjadi.env lalu isi. Berkas.env TIDAK pernah masuk repositori.
#
# DATABASE_URL boleh dikosongkan saat pengembangan. Bila kosong, aplikasi
# menyalakan PostgreSQL tersemat sendiri (lihat skrip/nyalakan_basisdata.py).
# Isi hanya untuk penempatan ke server sungguhan.
DATABASE_URL=
RAHASIA_JWT=ganti_dengan_hasil__openssl_rand_hex_32
ASAL_FRONTEND=http://localhost:5173
```

Tambahkan ke `.gitignore`:

```
# Data PostgreSQL pengembangan
backend/data_pg/
```

- [ ] **Langkah 4: Nyalakan dan pastikan hidup**

```bash
cd backend
uv sync --all-groups
uv run python -m skrip.nyalakan_basisdata
uv run python -c "
import psycopg
from skrip.nyalakan_basisdata import uri_basisdata_lokal
with psycopg.connect(uri_basisdata_lokal()) as c, c.cursor() as k:
    k.execute('SELECT version()')
    print(k.fetchone()[0][:40])
"
```

Diharapkan: tercetak `DATABASE_URL=...` lalu `PostgreSQL 16.x on x86_64-pc-linux-gnu`.

- [ ] **Langkah 5: Commit**

```bash
git add backend/pyproject.toml backend/skrip backend/.env.contoh backend/app/__init__.py.gitignore
git commit -m "chore: kerangka repositori dan PostgreSQL tersemat"
```

---

## Tugas 3: Konfigurasi, sesi basis data, dan endpoint kesehatan

**Berkas:**
- Buat: `backend/app/konfigurasi.py`, `backend/app/basisdata.py`, `backend/app/model/dasar.py`, `backend/app/main.py`, `backend/app/rute/sehat.py`, `backend/tests/conftest.py`, `backend/tests/test_sehat.py`

**Antarmuka:**
- Memakai: `DATABASE_URL`, `RAHASIA_JWT`, `ASAL_FRONTEND` dari Tugas 2.
- Menghasilkan: `pengaturan` (objek `Pengaturan`), `ambil_sesi()` (dependensi FastAPI menghasilkan `Session`), `buat_aplikasi() -> FastAPI`.

- [ ] **Langkah 1: Tulis `backend/app/konfigurasi.py`**

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Pengaturan(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = ""
    rahasia_jwt: str
    asal_frontend: str = "http://localhost:5173"
    umur_token_akses_menit: int = 15
    umur_token_segar_hari: int = 30


@lru_cache
def ambil_pengaturan() -> Pengaturan:
    return Pengaturan()  # type: ignore[call-arg]


def url_basisdata() -> str:
    """URL basis data yang dipakai aplikasi.

    Bila DATABASE_URL diisi, itu yang dipakai, jalur untuk penempatan.
    Bila kosong, PostgreSQL tersemat dinyalakan, jalur untuk pengembangan.
    """
    if ditetapkan := ambil_pengaturan().database_url:
        return ditetapkan

    from skrip.nyalakan_basisdata import uri_basisdata_lokal

    return uri_basisdata_lokal().replace("postgresql://", "postgresql+psycopg://", 1)
```

Cadangan ke PostgreSQL tersemat hanya berlaku saat `DATABASE_URL` **kosong**. Di penempatan, variabel itu selalu terisi, sehingga jalur tersemat tidak pernah tersentuh. Impornya sengaja ditaruh di dalam fungsi agar `pgserver` tidak ikut dimuat saat berjalan di server sungguhan.

- [ ] **Langkah 2: Tulis `backend/app/basisdata.py` dan `backend/app/model/dasar.py`**

```python
# app/basisdata.py
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
```

**Mesin dibuat malas, bukan saat modul diimpor.** Ini penyimpangan dari rancangan awal, dan alasannya baru terlihat saat uji dijalankan: `conftest.py` mengimpor modul ini untuk mengambil `ambil_sesi`, dan pembuatan mesin di tingkat modul akan **menyalakan basis data pengembangan hanya karena sebuah impor**, padahal uji memakai basis datanya sendiri. Efek samping saat impor selalu berakhir seperti ini.

```python
# app/model/dasar.py
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Dasar(DeclarativeBase):
    pass


class KolomWaktu:
    dibuat_pada: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    diubah_pada: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
        nullable=False, index=True,
    )
```

`Dasar` lahir di sini, bukan bersama tabel pertama, karena `conftest.py` di Langkah 4 sudah membutuhkannya untuk membangun basis data uji. `diubah_pada` diberi indeks sejak sekarang karena sinkronisasi beda-saja di M3 bergantung padanya ([05 §5.4](../perancangan/05-sinkronisasi-offline.md)).

- [ ] **Langkah 3: Tulis `backend/app/rute/sehat.py` dan `backend/app/main.py`**

```python
# app/rute/sehat.py
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.basisdata import ambil_sesi

rute = APIRouter(tags=["sehat"])


@rute.get("/sehat")
def sehat(sesi: Session = Depends(ambil_sesi)) -> dict[str, str]:
    sesi.execute(text("SELECT 1"))
    return {"status": "sehat"}
```

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.konfigurasi import ambil_pengaturan
from app.rute import sehat


def buat_aplikasi() -> FastAPI:
    aplikasi = FastAPI(title="Sistem Informasi Manajemen Toko", version="0.1.0")
    aplikasi.add_middleware(
        CORSMiddleware,
        allow_origins=[ambil_pengaturan().asal_frontend],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    aplikasi.include_router(sehat.rute, prefix="/api/v1")
    return aplikasi


app = buat_aplikasi()
```

CORS dibatasi ke satu asal, tidak pernah `*` ([08 §8.4](../perancangan/08-keamanan-dan-peran.md)).

- [ ] **Langkah 4: Tulis `backend/tests/conftest.py`**

```python
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
    """PostgreSQL 16 sungguhan, sekali pakai, di folder sementara."""
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
```

PostgreSQL sungguhan, bukan SQLite ([10 §10.3](../perancangan/10-strategi-pengujian.md)).

- [ ] **Langkah 5: Tulis `backend/tests/test_sehat.py` dan jalankan**

```python
from fastapi.testclient import TestClient


def test_sehat_menjawab_sehat(klien: TestClient) -> None:
    jawaban = klien.get("/api/v1/sehat")
    assert jawaban.status_code == 200
    assert jawaban.json() == {"status": "sehat"}
```

Jalankan: `cd backend && uv run pytest tests/test_sehat.py -v`
Diharapkan: LULUS

- [ ] **Langkah 6: Commit**

```bash
git add backend/app backend/tests
git commit -m "feat: konfigurasi, sesi basis data, dan endpoint kesehatan"
```

---

## Tugas 4: Alembic dan tabel pengguna

**Berkas:**
- Buat: `backend/alembic.ini`, `backend/migrasi/env.py`, `backend/app/model/pengguna.py`
- Uji: `backend/tests/test_model_pengguna.py`

**Antarmuka:**
- Memakai: `Dasar` dan `KolomWaktu` dari Tugas 3.
- Menghasilkan: `Pengguna` dengan kolom `id, nama_pengguna, nama_lengkap, sandi_hash, peran, aktif, dibuat_pada, diubah_pada`; enum `Peran` bernilai `pemilik` dan `kasir`.

- [ ] **Langkah 1: Tulis `backend/app/model/pengguna.py`**

```python
import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.model.dasar import Dasar, KolomWaktu


class Peran(str, enum.Enum):
    pemilik = "pemilik"
    kasir = "kasir"


class Pengguna(Dasar, KolomWaktu):
    __tablename__ = "pengguna"

    id: Mapped[int] = mapped_column(primary_key=True)
    nama_pengguna: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nama_lengkap: Mapped[str] = mapped_column(String(100), nullable=False)
    sandi_hash: Mapped[str] = mapped_column(nullable=False)
    peran: Mapped[Peran] = mapped_column(Enum(Peran, name="peran"), nullable=False)
    aktif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
```

- [ ] **Langkah 2: Siapkan Alembic**

```bash
cd backend
uv run alembic init migrasi
```

Sunting `migrasi/env.py`, ganti bagian target metadata dan URL:

```python
from app.konfigurasi import ambil_pengaturan
from app.model.dasar import Dasar
import app.model.pengguna  # noqa: F401  agar tabel terdaftar

target_metadata = Dasar.metadata
config.set_main_option("sqlalchemy.url", ambil_pengaturan().database_url)
```

- [ ] **Langkah 3: Bangkitkan dan terapkan migrasi**

```bash
uv run alembic revision --autogenerate -m "tabel pengguna"
uv run alembic upgrade head
uv run python -c "import psycopg; from skrip.nyalakan_basisdata import uri_basisdata_lokal;\
c=psycopg.connect(uri_basisdata_lokal()); k=c.cursor();\
k.execute(\"SELECT column_name FROM information_schema.columns WHERE table_name='pengguna'\");\
print([r[0] for r in k.fetchall()])"
```

Diharapkan: tabel `pengguna` tampil dengan kolom sesuai Langkah 1.

- [ ] **Langkah 4: Tulis uji dan jalankan**

```python
# tests/test_model_pengguna.py
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.model.pengguna import Pengguna, Peran


def test_nama_pengguna_wajib_unik(sesi: Session) -> None:
    sesi.add(Pengguna(nama_pengguna="irvan", nama_lengkap="Irvan",
                      sandi_hash="x", peran=Peran.pemilik))
    sesi.commit()
    sesi.add(Pengguna(nama_pengguna="irvan", nama_lengkap="Irvan Lain",
                      sandi_hash="y", peran=Peran.kasir))
    with pytest.raises(IntegrityError):
        sesi.commit()


def test_pengguna_baru_aktif_secara_bawaan(sesi: Session) -> None:
    p = Pengguna(nama_pengguna="kasir1", nama_lengkap="Kasir Satu",
                 sandi_hash="x", peran=Peran.kasir)
    sesi.add(p)
    sesi.commit()
    assert p.aktif is True
```

Jalankan: `uv run pytest tests/test_model_pengguna.py -v` → LULUS

- [ ] **Langkah 5: Commit**

```bash
git add backend/alembic.ini backend/migrasi backend/app/model backend/tests
git commit -m "feat: tabel pengguna dan migrasi pertama"
```

---

## Tugas 5: Hash sandi Argon2

**Berkas:**
- Buat: `backend/app/keamanan/sandi.py`
- Uji: `backend/tests/test_sandi.py`

**Antarmuka:**
- Menghasilkan: `hash_sandi(sandi: str) -> str`, `verifikasi_sandi(sandi: str, hash_tersimpan: str) -> bool`.

- [ ] **Langkah 1: Tulis `backend/app/keamanan/sandi.py`**

```python
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_pengurai = PasswordHasher()


def hash_sandi(sandi: str) -> str:
    return _pengurai.hash(sandi)


def verifikasi_sandi(sandi: str, hash_tersimpan: str) -> bool:
    try:
        return _pengurai.verify(hash_tersimpan, sandi)
    except VerifyMismatchError:
        return False
```

Hanya `VerifyMismatchError` yang ditangkap. Hash rusak melempar kesalahan lain dan **harus** naik, sesuai larangan menelan kesalahan ([09 §9.5](../perancangan/09-penanganan-error.md)).

- [ ] **Langkah 2: Tulis uji**

```python
# tests/test_sandi.py
import pytest
from argon2.exceptions import InvalidHashError

from app.keamanan.sandi import hash_sandi, verifikasi_sandi


def test_sandi_benar_diterima() -> None:
    assert verifikasi_sandi("rahasia123", hash_sandi("rahasia123")) is True


def test_sandi_salah_ditolak() -> None:
    assert verifikasi_sandi("salah", hash_sandi("rahasia123")) is False


def test_hash_selalu_berbeda_meski_sandi_sama() -> None:
    assert hash_sandi("rahasia123") != hash_sandi("rahasia123")


def test_sandi_tidak_pernah_tampak_di_hash() -> None:
    assert "rahasia123" not in hash_sandi("rahasia123")


def test_hash_rusak_melempar_kesalahan_bukan_false() -> None:
    with pytest.raises(InvalidHashError):
        verifikasi_sandi("apa pun", "bukan-hash-argon2")
```

- [ ] **Langkah 3: Jalankan uji**

Jalankan: `uv run pytest tests/test_sandi.py -v`
Diharapkan: 5 LULUS

- [ ] **Langkah 4: Commit**

```bash
git add backend/app/keamanan/sandi.py backend/tests/test_sandi.py
git commit -m "feat: hash sandi Argon2"
```

---

## Tugas 6: Token akses dan token segar berotasi

**Berkas:**
- Buat: `backend/app/keamanan/token.py`, `backend/app/model/token.py`
- Uji: `backend/tests/test_token.py`
- Migrasi: `backend/migrasi/versions/` (dibangkitkan)

**Antarmuka:**
- Memakai: `ambil_pengaturan()` dari Tugas 3.
- Menghasilkan: `terbitkan_token_akses(pengguna_id: int, peran: str) -> str`, `baca_token_akses(token: str) -> IsiToken`, `IsiToken` (dataclass dengan `pengguna_id: int`, `peran: str`), model `TokenSegar` dengan kolom `id, pengguna_id, token_hash, kedaluwarsa_pada, dicabut_pada, dibuat_pada`, dan kesalahan `TokenTidakSah`.

- [ ] **Langkah 1: Tulis `backend/app/model/token.py`**

```python
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.model.dasar import Dasar, KolomWaktu


class TokenSegar(Dasar, KolomWaktu):
    __tablename__ = "token_segar"

    id: Mapped[int] = mapped_column(primary_key=True)
    pengguna_id: Mapped[int] = mapped_column(ForeignKey("pengguna.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    kedaluwarsa_pada: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dicabut_pada: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
```

Yang disimpan adalah hash SHA-256 token, bukan tokennya. Basis data yang bocor tidak menyerahkan sesi siapa pun.

- [ ] **Langkah 2: Tulis `backend/app/keamanan/token.py`**

```python
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
    try:
        muatan = jwt.decode(token, ambil_pengaturan().rahasia_jwt, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise TokenTidakSah(str(e)) from e
    return IsiToken(pengguna_id=int(muatan["sub"]), peran=muatan["peran"])


def buat_token_segar() -> tuple[str, str]:
    """Menghasilkan (token_mentah, token_hash). Hanya hash yang disimpan."""
    mentah = secrets.token_urlsafe(48)
    return mentah, hashlib.sha256(mentah.encode()).hexdigest()


def hash_token_segar(mentah: str) -> str:
    return hashlib.sha256(mentah.encode()).hexdigest()
```

- [ ] **Langkah 3: Bangkitkan migrasi**

```bash
cd backend
uv run alembic revision --autogenerate -m "tabel token segar"
uv run alembic upgrade head
```

- [ ] **Langkah 4: Tulis uji**

```python
# tests/test_token.py
import time

import pytest

from app.keamanan.token import (
    TokenTidakSah, baca_token_akses, buat_token_segar,
    hash_token_segar, terbitkan_token_akses,
)


def test_token_bisa_dibaca_kembali() -> None:
    isi = baca_token_akses(terbitkan_token_akses(7, "pemilik"))
    assert isi.pengguna_id == 7
    assert isi.peran == "pemilik"


def test_token_asing_ditolak() -> None:
    with pytest.raises(TokenTidakSah):
        baca_token_akses("bukan.token.sah")


def test_token_yang_diubah_ditolak() -> None:
    token = terbitkan_token_akses(7, "kasir")
    rusak = token[:-3] + ("aaa" if not token.endswith("aaa") else "bbb")
    with pytest.raises(TokenTidakSah):
        baca_token_akses(rusak)


def test_token_kedaluwarsa_ditolak(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.konfigurasi import ambil_pengaturan
    ambil_pengaturan.cache_clear()
    monkeypatch.setenv("UMUR_TOKEN_AKSES_MENIT", "0")
    token = terbitkan_token_akses(7, "kasir")
    time.sleep(1)
    with pytest.raises(TokenTidakSah):
        baca_token_akses(token)
    ambil_pengaturan.cache_clear()


def test_token_segar_disimpan_sebagai_hash() -> None:
    mentah, ter_hash = buat_token_segar()
    assert mentah != ter_hash
    assert hash_token_segar(mentah) == ter_hash
    assert len(ter_hash) == 64
```

- [ ] **Langkah 5: Jalankan uji**

Jalankan: `uv run pytest tests/test_token.py -v`
Diharapkan: 5 LULUS

- [ ] **Langkah 6: Commit**

```bash
git add backend/app/keamanan/token.py backend/app/model/token.py backend/migrasi backend/tests/test_token.py
git commit -m "feat: token akses JWT dan token segar tersimpan sebagai hash"
```

---

## Tugas 7: Bentuk kesalahan seragam

**Berkas:**
- Buat: `backend/app/kesalahan.py`
- Modifikasi: `backend/app/main.py`
- Uji: `backend/tests/test_kesalahan.py`

**Antarmuka:**
- Menghasilkan: `KesalahanDomain(kode: str, pesan: str, status: int = 422, detail: dict | None = None)` dan handler yang mengubahnya menjadi `{kode, pesan, detail}`.

- [ ] **Langkah 1: Tulis `backend/app/kesalahan.py`**

```python
from typing import Any


class KesalahanDomain(Exception):
    """Kegagalan yang diperkirakan, punya kode dan pesan berbahasa Indonesia."""

    def __init__(self, kode: str, pesan: str, status: int = 422,
                 detail: dict[str, Any] | None = None) -> None:
        super().__init__(pesan)
        self.kode = kode
        self.pesan = pesan
        self.status = status
        self.detail = detail or {}

    def sebagai_jawaban(self) -> dict[str, Any]:
        return {"kode": self.kode, "pesan": self.pesan, "detail": self.detail}


class KredensialSalah(KesalahanDomain):
    def __init__(self) -> None:
        super().__init__("KREDENSIAL_SALAH", "Nama pengguna atau sandi keliru", status=401)


class TidakBerhak(KesalahanDomain):
    def __init__(self) -> None:
        super().__init__("TIDAK_BERHAK", "Peran Anda tidak mengizinkan tindakan ini", status=403)


class PemilikTerakhir(KesalahanDomain):
    def __init__(self) -> None:
        super().__init__(
            "PEMILIK_TERAKHIR",
            "Tindakan ini menyisakan nol akun pemilik aktif. Tunjuk pemilik lain lebih dulu.",
        )


class PeranSendiri(KesalahanDomain):
    def __init__(self) -> None:
        super().__init__("PERAN_SENDIRI", "Anda tidak bisa mengubah peran akun Anda sendiri")


class TerlaluBanyakPercobaan(KesalahanDomain):
    def __init__(self, menit: int) -> None:
        super().__init__(
            "TERLALU_BANYAK_PERCOBAAN",
            f"Terlalu banyak percobaan masuk. Coba lagi dalam {menit} menit.",
            status=429,
        )
```

- [ ] **Langkah 2: Pasang handler di `backend/app/main.py`**

Tambahkan di dalam `buat_aplikasi()` sebelum `return`:

```python
from fastapi import Request
from fastapi.responses import JSONResponse

from app.kesalahan import KesalahanDomain

    @aplikasi.exception_handler(KesalahanDomain)
    async def tangani_kesalahan_domain(_: Request, e: KesalahanDomain) -> JSONResponse:
        return JSONResponse(status_code=e.status, content=e.sebagai_jawaban())
```

- [ ] **Langkah 3: Tulis uji**

```python
# tests/test_kesalahan.py
from app.kesalahan import KredensialSalah, PemilikTerakhir


def test_bentuk_jawaban_seragam() -> None:
    jawaban = KredensialSalah().sebagai_jawaban()
    assert set(jawaban) == {"kode", "pesan", "detail"}
    assert jawaban["kode"] == "KREDENSIAL_SALAH"


def test_pesan_berbahasa_indonesia_dan_menyebut_langkah_berikutnya() -> None:
    pesan = PemilikTerakhir().pesan
    assert "pemilik" in pesan.lower()
    assert "lebih dulu" in pesan.lower()
```

- [ ] **Langkah 4: Jalankan uji**

Jalankan: `uv run pytest tests/test_kesalahan.py -v` → 2 LULUS

- [ ] **Langkah 5: Commit**

```bash
git add backend/app/kesalahan.py backend/app/main.py backend/tests/test_kesalahan.py
git commit -m "feat: bentuk kesalahan seragam berbahasa Indonesia"
```

---

## Tugas 8: Layanan otentikasi dan pembatasan percobaan masuk

**Berkas:**
- Buat: `backend/app/layanan/otentikasi.py`, `backend/app/model/percobaan_masuk.py`
- Uji: `backend/tests/test_otentikasi.py`

**Antarmuka:**
- Memakai: `verifikasi_sandi` (Tugas 5), `terbitkan_token_akses`, `buat_token_segar`, `hash_token_segar` (Tugas 6), `KredensialSalah`, `TerlaluBanyakPercobaan` (Tugas 7).
- Menghasilkan: `masuk(sesi, nama_pengguna, sandi, alamat_ip) -> PasanganToken`, `segarkan(sesi, token_segar_mentah) -> PasanganToken`, `keluar(sesi, token_segar_mentah) -> None`, dataclass `PasanganToken(token_akses: str, token_segar: str)`.

- [ ] **Langkah 1: Tulis `backend/app/model/percobaan_masuk.py`**

```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.model.dasar import Dasar, KolomWaktu


class PercobaanMasuk(Dasar, KolomWaktu):
    __tablename__ = "percobaan_masuk"

    id: Mapped[int] = mapped_column(primary_key=True)
    nama_pengguna: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    alamat_ip: Mapped[str] = mapped_column(String(45), index=True, nullable=False)
    berhasil: Mapped[bool] = mapped_column(default=False, nullable=False)
```

Bangkitkan migrasi: `uv run alembic revision --autogenerate -m "tabel percobaan masuk" && uv run alembic upgrade head`

- [ ] **Langkah 2: Tulis `backend/app/layanan/otentikasi.py`**

```python
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.kesalahan import KredensialSalah, TerlaluBanyakPercobaan
from app.keamanan.sandi import verifikasi_sandi
from app.keamanan.token import (
    buat_token_segar, hash_token_segar, terbitkan_token_akses,
)
from app.konfigurasi import ambil_pengaturan
from app.model.percobaan_masuk import PercobaanMasuk
from app.model.pengguna import Pengguna
from app.model.token import TokenSegar

BATAS_PERCOBAAN = 5
JENDELA_MENIT = 15


@dataclass(frozen=True)
class PasanganToken:
    token_akses: str
    token_segar: str


def _percobaan_gagal_terakhir(sesi: Session, nama_pengguna: str, alamat_ip: str) -> int:
    sejak = datetime.now(UTC) - timedelta(minutes=JENDELA_MENIT)
    kueri = select(PercobaanMasuk).where(
        PercobaanMasuk.berhasil.is_(False),
        PercobaanMasuk.dibuat_pada >= sejak,
        (PercobaanMasuk.nama_pengguna == nama_pengguna)
        | (PercobaanMasuk.alamat_ip == alamat_ip),
    )
    return len(sesi.execute(kueri).scalars().all())


def _terbitkan_pasangan(sesi: Session, pengguna: Pengguna) -> PasanganToken:
    mentah, ter_hash = buat_token_segar()
    sesi.add(TokenSegar(
        pengguna_id=pengguna.id,
        token_hash=ter_hash,
        kedaluwarsa_pada=datetime.now(UTC)
        + timedelta(days=ambil_pengaturan().umur_token_segar_hari),
    ))
    sesi.flush()
    return PasanganToken(
        token_akses=terbitkan_token_akses(pengguna.id, pengguna.peran.value),
        token_segar=mentah,
    )


def masuk(sesi: Session, nama_pengguna: str, sandi: str, alamat_ip: str) -> PasanganToken:
    if _percobaan_gagal_terakhir(sesi, nama_pengguna, alamat_ip) >= BATAS_PERCOBAAN:
        raise TerlaluBanyakPercobaan(JENDELA_MENIT)

    pengguna = sesi.execute(
        select(Pengguna).where(Pengguna.nama_pengguna == nama_pengguna)
    ).scalar_one_or_none()

    sah = (
        pengguna is not None
        and pengguna.aktif
        and verifikasi_sandi(sandi, pengguna.sandi_hash)
    )
    sesi.add(PercobaanMasuk(nama_pengguna=nama_pengguna, alamat_ip=alamat_ip, berhasil=sah))
    if not sah or pengguna is None:
        sesi.commit()
        raise KredensialSalah

    pasangan = _terbitkan_pasangan(sesi, pengguna)
    sesi.commit()
    return pasangan


def segarkan(sesi: Session, token_segar_mentah: str) -> PasanganToken:
    ter_hash = hash_token_segar(token_segar_mentah)
    baris = sesi.execute(
        select(TokenSegar).where(TokenSegar.token_hash == ter_hash)
    ).scalar_one_or_none()

    if baris is None or baris.kedaluwarsa_pada < datetime.now(UTC):
        raise KredensialSalah

    if baris.dicabut_pada is not None:
        # Token yang sudah dicabut dipakai lagi: pertanda dicuri.
        # Cabut SELURUH sesi pengguna itu.
        for lain in sesi.execute(
            select(TokenSegar).where(TokenSegar.pengguna_id == baris.pengguna_id)
        ).scalars():
            lain.dicabut_pada = datetime.now(UTC)
        sesi.commit()
        raise KredensialSalah

    baris.dicabut_pada = datetime.now(UTC)
    pengguna = sesi.get(Pengguna, baris.pengguna_id)
    if pengguna is None or not pengguna.aktif:
        sesi.commit()
        raise KredensialSalah

    pasangan = _terbitkan_pasangan(sesi, pengguna)
    sesi.commit()
    return pasangan


def keluar(sesi: Session, token_segar_mentah: str) -> None:
    baris = sesi.execute(
        select(TokenSegar).where(TokenSegar.token_hash == hash_token_segar(token_segar_mentah))
    ).scalar_one_or_none()
    if baris is not None and baris.dicabut_pada is None:
        baris.dicabut_pada = datetime.now(UTC)
    sesi.commit()
```

- [ ] **Langkah 3: Tulis uji**

```python
# tests/test_otentikasi.py
import pytest
from sqlalchemy.orm import Session

from app.kesalahan import KredensialSalah, TerlaluBanyakPercobaan
from app.keamanan.sandi import hash_sandi
from app.layanan.otentikasi import BATAS_PERCOBAAN, keluar, masuk, segarkan
from app.model.pengguna import Pengguna, Peran

IP = "127.0.0.1"


@pytest.fixture
def pemilik(sesi: Session) -> Pengguna:
    p = Pengguna(nama_pengguna="irvan", nama_lengkap="Irvan",
                 sandi_hash=hash_sandi("rahasia123"), peran=Peran.pemilik)
    sesi.add(p)
    sesi.commit()
    return p


def test_masuk_dengan_sandi_benar(sesi: Session, pemilik: Pengguna) -> None:
    pasangan = masuk(sesi, "irvan", "rahasia123", IP)
    assert pasangan.token_akses
    assert pasangan.token_segar


def test_masuk_dengan_sandi_salah_ditolak(sesi: Session, pemilik: Pengguna) -> None:
    with pytest.raises(KredensialSalah):
        masuk(sesi, "irvan", "salah", IP)


def test_akun_nonaktif_tidak_bisa_masuk(sesi: Session, pemilik: Pengguna) -> None:
    pemilik.aktif = False
    sesi.commit()
    with pytest.raises(KredensialSalah):
        masuk(sesi, "irvan", "rahasia123", IP)


def test_percobaan_berlebih_diblokir(sesi: Session, pemilik: Pengguna) -> None:
    for _ in range(BATAS_PERCOBAAN):
        with pytest.raises(KredensialSalah):
            masuk(sesi, "irvan", "salah", IP)
    with pytest.raises(TerlaluBanyakPercobaan):
        masuk(sesi, "irvan", "rahasia123", IP)


def test_token_segar_berotasi(sesi: Session, pemilik: Pengguna) -> None:
    pertama = masuk(sesi, "irvan", "rahasia123", IP)
    kedua = segarkan(sesi, pertama.token_segar)
    assert kedua.token_segar != pertama.token_segar


def test_token_segar_lama_tidak_bisa_dipakai_ulang(sesi: Session, pemilik: Pengguna) -> None:
    pertama = masuk(sesi, "irvan", "rahasia123", IP)
    segarkan(sesi, pertama.token_segar)
    with pytest.raises(KredensialSalah):
        segarkan(sesi, pertama.token_segar)


def test_pemakaian_ulang_mencabut_seluruh_sesi(sesi: Session, pemilik: Pengguna) -> None:
    pertama = masuk(sesi, "irvan", "rahasia123", IP)
    kedua = segarkan(sesi, pertama.token_segar)
    with pytest.raises(KredensialSalah):
        segarkan(sesi, pertama.token_segar)   # token lama dipakai lagi
    with pytest.raises(KredensialSalah):
        segarkan(sesi, kedua.token_segar)     # sesi yang masih hidup ikut dicabut


def test_keluar_mencabut_token(sesi: Session, pemilik: Pengguna) -> None:
    pasangan = masuk(sesi, "irvan", "rahasia123", IP)
    keluar(sesi, pasangan.token_segar)
    with pytest.raises(KredensialSalah):
        segarkan(sesi, pasangan.token_segar)
```

- [ ] **Langkah 4: Jalankan uji**

Jalankan: `uv run pytest tests/test_otentikasi.py -v`
Diharapkan: 8 LULUS

- [ ] **Langkah 5: Commit**

```bash
git add backend/app/layanan backend/app/model/percobaan_masuk.py backend/migrasi backend/tests/test_otentikasi.py
git commit -m "feat: layanan otentikasi, rotasi token, dan pembatasan percobaan masuk"
```

---

## Tugas 9: Dependensi hak akses berbasis peran

**Berkas:**
- Buat: `backend/app/keamanan/hak_akses.py`
- Uji: `backend/tests/test_hak_akses.py`

**Antarmuka:**
- Memakai: `baca_token_akses`, `TokenTidakSah` (Tugas 6), `TidakBerhak` (Tugas 7).
- Menghasilkan: `pengguna_berjalan(...) -> Pengguna` (dependensi), `wajib_pemilik(...) -> Pengguna` (dependensi).

- [ ] **Langkah 1: Tulis `backend/app/keamanan/hak_akses.py`**

```python
from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.basisdata import ambil_sesi
from app.kesalahan import KesalahanDomain, TidakBerhak
from app.keamanan.token import TokenTidakSah, baca_token_akses
from app.model.pengguna import Pengguna, Peran


def pengguna_berjalan(
    authorization: str = Header(default=""),
    sesi: Session = Depends(ambil_sesi),
) -> Pengguna:
    if not authorization.startswith("Bearer "):
        raise KesalahanDomain("TOKEN_TIDAK_ADA", "Silakan masuk terlebih dahulu", status=401)
    try:
        isi = baca_token_akses(authorization.removeprefix("Bearer "))
    except TokenTidakSah as e:
        raise KesalahanDomain(
            "TOKEN_TIDAK_SAH", "Sesi Anda telah berakhir. Silakan masuk lagi.", status=401
        ) from e

    pengguna = sesi.get(Pengguna, isi.pengguna_id)
    if pengguna is None or not pengguna.aktif:
        raise KesalahanDomain(
            "TOKEN_TIDAK_SAH", "Sesi Anda telah berakhir. Silakan masuk lagi.", status=401
        )
    return pengguna


def wajib_pemilik(pengguna: Pengguna = Depends(pengguna_berjalan)) -> Pengguna:
    if pengguna.peran is not Peran.pemilik:
        raise TidakBerhak
    return pengguna
```

Peran dibaca ulang dari basis data, bukan dipercaya dari isi token. Akun yang dinonaktifkan langsung kehilangan akses tanpa menunggu tokennya kedaluwarsa.

- [ ] **Langkah 2: Tulis uji**

```python
# tests/test_hak_akses.py
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.keamanan.sandi import hash_sandi
from app.keamanan.token import terbitkan_token_akses
from app.model.pengguna import Pengguna, Peran


def _buat(sesi: Session, nama: str, peran: Peran) -> Pengguna:
    p = Pengguna(nama_pengguna=nama, nama_lengkap=nama.title(),
                 sandi_hash=hash_sandi("rahasia123"), peran=peran)
    sesi.add(p)
    sesi.commit()
    return p


def test_tanpa_token_ditolak(klien: TestClient) -> None:
    assert klien.get("/api/v1/pengguna").status_code == 401


def test_kasir_ditolak_di_endpoint_pemilik(klien: TestClient, sesi: Session) -> None:
    kasir = _buat(sesi, "kasir1", Peran.kasir)
    token = terbitkan_token_akses(kasir.id, "kasir")
    jawaban = klien.get("/api/v1/pengguna", headers={"Authorization": f"Bearer {token}"})
    assert jawaban.status_code == 403
    assert jawaban.json()["kode"] == "TIDAK_BERHAK"


def test_peran_dibaca_dari_basis_data_bukan_token(klien: TestClient, sesi: Session) -> None:
    kasir = _buat(sesi, "kasir2", Peran.kasir)
    token_palsu = terbitkan_token_akses(kasir.id, "pemilik")  # peran dipalsukan
    jawaban = klien.get("/api/v1/pengguna", headers={"Authorization": f"Bearer {token_palsu}"})
    assert jawaban.status_code == 403


def test_akun_nonaktif_langsung_kehilangan_akses(klien: TestClient, sesi: Session) -> None:
    pemilik = _buat(sesi, "irvan", Peran.pemilik)
    token = terbitkan_token_akses(pemilik.id, "pemilik")
    pemilik.aktif = False
    sesi.commit()
    assert klien.get(
        "/api/v1/pengguna", headers={"Authorization": f"Bearer {token}"}
    ).status_code == 401
```

- [ ] **Langkah 3: Jalankan uji**

Uji ini bergantung pada endpoint `/pengguna` dari Tugas 10. Jalankan setelah Tugas 10 selesai:
`uv run pytest tests/test_hak_akses.py -v` → 4 LULUS

- [ ] **Langkah 4: Commit**

```bash
git add backend/app/keamanan/hak_akses.py backend/tests/test_hak_akses.py
git commit -m "feat: dependensi hak akses berbasis peran"
```

---

## Tugas 10: Pengelolaan akun pengguna (AKS-01 sampai AKS-05)

**Berkas:**
- Buat: `backend/app/layanan/pengguna.py`, `backend/app/skema/pengguna.py`, `backend/app/rute/pengguna.py`
- Modifikasi: `backend/app/main.py`
- Uji: `backend/tests/test_pengguna.py`

**Antarmuka:**
- Memakai: `hash_sandi` (Tugas 5), `PemilikTerakhir`, `PeranSendiri` (Tugas 7), `wajib_pemilik` (Tugas 9).
- Menghasilkan: `buat_pengguna(sesi, data) -> Pengguna` (AKS-01), `ubah_pengguna(sesi, pengguna_id, data, oleh) -> Pengguna` (AKS-02, AKS-05), `atur_ulang_sandi(sesi, pengguna_id, sandi_baru) -> None` (AKS-03), `daftar_pengguna(sesi) -> list[Pengguna]`.

`buat_pengguna` **tidak** menerima `oleh`, karena pembuatan akun tidak punya penjagaan yang bergantung pada siapa pelakunya. `ubah_pengguna` menerimanya karena penjagaan AKS-05 dan `PERAN_SENDIRI` perlu tahu siapa yang bertindak.

- [ ] **Langkah 1: Tulis `backend/app/skema/pengguna.py`**

```python
from pydantic import BaseModel, ConfigDict, Field

from app.model.pengguna import Peran


class PenggunaKeluar(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nama_pengguna: str
    nama_lengkap: str
    peran: Peran
    aktif: bool


class BuatPengguna(BaseModel):
    nama_pengguna: str = Field(min_length=3, max_length=50)
    nama_lengkap: str = Field(min_length=1, max_length=100)
    sandi: str = Field(min_length=8)
    peran: Peran


class UbahPengguna(BaseModel):
    nama_lengkap: str | None = Field(default=None, min_length=1, max_length=100)
    peran: Peran | None = None
    aktif: bool | None = None


class AturUlangSandi(BaseModel):
    sandi_baru: str = Field(min_length=8)
```

- [ ] **Langkah 2: Tulis `backend/app/layanan/pengguna.py`**

```python
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.kesalahan import KesalahanDomain, PemilikTerakhir, PeranSendiri
from app.keamanan.sandi import hash_sandi
from app.model.pengguna import Pengguna, Peran
from app.skema.pengguna import BuatPengguna, UbahPengguna


def _jumlah_pemilik_aktif(sesi: Session, kecuali_id: int | None = None) -> int:
    kueri = select(func.count()).select_from(Pengguna).where(
        Pengguna.peran == Peran.pemilik, Pengguna.aktif.is_(True)
    )
    if kecuali_id is not None:
        kueri = kueri.where(Pengguna.id != kecuali_id)
    return sesi.execute(kueri).scalar_one()


def daftar_pengguna(sesi: Session) -> list[Pengguna]:
    return list(sesi.execute(select(Pengguna).order_by(Pengguna.nama_pengguna)).scalars())


def buat_pengguna(sesi: Session, data: BuatPengguna) -> Pengguna:
    sudah_ada = sesi.execute(
        select(Pengguna).where(Pengguna.nama_pengguna == data.nama_pengguna)
    ).scalar_one_or_none()
    if sudah_ada is not None:
        raise KesalahanDomain(
            "NAMA_PENGGUNA_TERPAKAI",
            f"Nama pengguna {data.nama_pengguna} sudah dipakai. Pilih nama lain.",
            detail={"nama_pengguna": data.nama_pengguna},
        )

    pengguna = Pengguna(
        nama_pengguna=data.nama_pengguna,
        nama_lengkap=data.nama_lengkap,
        sandi_hash=hash_sandi(data.sandi),
        peran=data.peran,
    )
    sesi.add(pengguna)
    sesi.commit()
    return pengguna


def ubah_pengguna(sesi: Session, pengguna_id: int, data: UbahPengguna,
                  oleh: Pengguna) -> Pengguna:
    pengguna = sesi.get(Pengguna, pengguna_id)
    if pengguna is None:
        raise KesalahanDomain("PENGGUNA_TIDAK_DITEMUKAN", "Akun tidak ditemukan", status=404)

    if data.peran is not None and pengguna.id == oleh.id and data.peran != pengguna.peran:
        raise PeranSendiri

    akan_pemilik_aktif = (
        (data.peran or pengguna.peran) is Peran.pemilik
        and (pengguna.aktif if data.aktif is None else data.aktif)
    )
    if not akan_pemilik_aktif and _jumlah_pemilik_aktif(sesi, kecuali_id=pengguna.id) == 0:
        raise PemilikTerakhir

    if data.nama_lengkap is not None:
        pengguna.nama_lengkap = data.nama_lengkap
    if data.peran is not None:
        pengguna.peran = data.peran
    if data.aktif is not None:
        pengguna.aktif = data.aktif

    sesi.commit()
    return pengguna


def atur_ulang_sandi(sesi: Session, pengguna_id: int, sandi_baru: str) -> None:
    pengguna = sesi.get(Pengguna, pengguna_id)
    if pengguna is None:
        raise KesalahanDomain("PENGGUNA_TIDAK_DITEMUKAN", "Akun tidak ditemukan", status=404)
    pengguna.sandi_hash = hash_sandi(sandi_baru)
    sesi.commit()
```

> **Penjagaan yang ditunda ke M2.** [Bab 08](../perancangan/08-keamanan-dan-peran.md) juga menuntut penolakan `SESI_KAS_MASIH_TERBUKA` saat menonaktifkan akun yang sesi kasnya belum ditutup. Tabel `sesi_kas` baru lahir di M2, jadi penjagaan itu **ditambahkan di M2**, bukan sekarang. Jangan menulis kode setengah jadi untuknya di M0.

- [ ] **Langkah 3: Tulis `backend/app/rute/pengguna.py` dan pasang di `main.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.basisdata import ambil_sesi
from app.keamanan.hak_akses import wajib_pemilik
from app.layanan import pengguna as layanan
from app.model.pengguna import Pengguna
from app.skema.pengguna import AturUlangSandi, BuatPengguna, PenggunaKeluar, UbahPengguna

rute = APIRouter(prefix="/pengguna", tags=["pengguna"])


@rute.get("", response_model=list[PenggunaKeluar])
def daftar(sesi: Session = Depends(ambil_sesi),
           _: Pengguna = Depends(wajib_pemilik)) -> list[Pengguna]:
    return layanan.daftar_pengguna(sesi)


@rute.post("", response_model=PenggunaKeluar, status_code=201)
def buat(data: BuatPengguna, sesi: Session = Depends(ambil_sesi),
         _: Pengguna = Depends(wajib_pemilik)) -> Pengguna:
    return layanan.buat_pengguna(sesi, data)


@rute.patch("/{pengguna_id}", response_model=PenggunaKeluar)
def ubah(pengguna_id: int, data: UbahPengguna, sesi: Session = Depends(ambil_sesi),
         oleh: Pengguna = Depends(wajib_pemilik)) -> Pengguna:
    return layanan.ubah_pengguna(sesi, pengguna_id, data, oleh)


@rute.post("/{pengguna_id}/atur-ulang-sandi", status_code=204)
def atur_ulang(pengguna_id: int, data: AturUlangSandi,
               sesi: Session = Depends(ambil_sesi),
               _: Pengguna = Depends(wajib_pemilik)) -> None:
    layanan.atur_ulang_sandi(sesi, pengguna_id, data.sandi_baru)
```

Di `main.py`, tambahkan `from app.rute import pengguna` dan `aplikasi.include_router(pengguna.rute, prefix="/api/v1")`.

Perhatikan rute tidak memuat satu pun aturan bisnis (G6).

- [ ] **Langkah 4: Tulis uji**

```python
# tests/test_pengguna.py
import pytest
from sqlalchemy.orm import Session

from app.kesalahan import KesalahanDomain, PemilikTerakhir, PeranSendiri
from app.keamanan.sandi import hash_sandi, verifikasi_sandi
from app.layanan.pengguna import atur_ulang_sandi, buat_pengguna, ubah_pengguna
from app.model.pengguna import Pengguna, Peran
from app.skema.pengguna import BuatPengguna, UbahPengguna


@pytest.fixture
def pemilik(sesi: Session) -> Pengguna:
    p = Pengguna(nama_pengguna="irvan", nama_lengkap="Irvan",
                 sandi_hash=hash_sandi("rahasia123"), peran=Peran.pemilik)
    sesi.add(p)
    sesi.commit()
    return p


def test_buat_akun_kasir(sesi: Session, pemilik: Pengguna) -> None:
    kasir = buat_pengguna(sesi, BuatPengguna(
        nama_pengguna="kasir1", nama_lengkap="Kasir Satu",
        sandi="rahasia123", peran=Peran.kasir))
    assert kasir.peran is Peran.kasir
    assert kasir.aktif is True
    assert kasir.sandi_hash != "rahasia123"


def test_nama_pengguna_ganda_ditolak(sesi: Session, pemilik: Pengguna) -> None:
    with pytest.raises(KesalahanDomain) as e:
        buat_pengguna(sesi, BuatPengguna(
            nama_pengguna="irvan", nama_lengkap="Irvan Lain",
            sandi="rahasia123", peran=Peran.kasir))
    assert e.value.kode == "NAMA_PENGGUNA_TERPAKAI"


def test_menonaktifkan_pemilik_terakhir_ditolak(sesi: Session, pemilik: Pengguna) -> None:
    with pytest.raises(PemilikTerakhir):
        ubah_pengguna(sesi, pemilik.id, UbahPengguna(aktif=False), oleh=pemilik)


def test_menurunkan_peran_pemilik_terakhir_ditolak(sesi: Session, pemilik: Pengguna) -> None:
    lain = buat_pengguna(sesi, BuatPengguna(
        nama_pengguna="admin2", nama_lengkap="Admin Dua",
        sandi="rahasia123", peran=Peran.pemilik))
    lain.aktif = False
    sesi.commit()
    with pytest.raises(PemilikTerakhir):
        ubah_pengguna(sesi, pemilik.id, UbahPengguna(peran=Peran.kasir), oleh=lain)


def test_mengubah_peran_sendiri_ditolak(sesi: Session, pemilik: Pengguna) -> None:
    buat_pengguna(sesi, BuatPengguna(
        nama_pengguna="admin2", nama_lengkap="Admin Dua",
        sandi="rahasia123", peran=Peran.pemilik))
    with pytest.raises(PeranSendiri):
        ubah_pengguna(sesi, pemilik.id, UbahPengguna(peran=Peran.kasir), oleh=pemilik)


def test_menonaktifkan_pemilik_boleh_bila_masih_ada_pemilik_lain(
    sesi: Session, pemilik: Pengguna
) -> None:
    lain = buat_pengguna(sesi, BuatPengguna(
        nama_pengguna="admin2", nama_lengkap="Admin Dua",
        sandi="rahasia123", peran=Peran.pemilik))
    hasil = ubah_pengguna(sesi, pemilik.id, UbahPengguna(aktif=False), oleh=lain)
    assert hasil.aktif is False


def test_akun_dinonaktifkan_bukan_dihapus(sesi: Session, pemilik: Pengguna) -> None:
    kasir = buat_pengguna(sesi, BuatPengguna(
        nama_pengguna="kasir1", nama_lengkap="Kasir Satu",
        sandi="rahasia123", peran=Peran.kasir))
    ubah_pengguna(sesi, kasir.id, UbahPengguna(aktif=False), oleh=pemilik)
    assert sesi.get(Pengguna, kasir.id) is not None


def test_atur_ulang_sandi(sesi: Session, pemilik: Pengguna) -> None:
    kasir = buat_pengguna(sesi, BuatPengguna(
        nama_pengguna="kasir1", nama_lengkap="Kasir Satu",
        sandi="rahasia123", peran=Peran.kasir))
    atur_ulang_sandi(sesi, kasir.id, "sandibaru456")
    sesi.refresh(kasir)
    assert verifikasi_sandi("sandibaru456", kasir.sandi_hash) is True
```

- [ ] **Langkah 5: Jalankan seluruh uji backend**

Jalankan: `uv run pytest -v`
Diharapkan: seluruh uji LULUS, termasuk `test_hak_akses.py` dari Tugas 9 yang kini punya endpoint sasaran.

- [ ] **Langkah 6: Commit**

```bash
git add backend/app/layanan/pengguna.py backend/app/skema backend/app/rute/pengguna.py backend/app/main.py backend/tests/test_pengguna.py
git commit -m "feat: pengelolaan akun pengguna beserta penjagaan pemilik terakhir"
```

---

## Tugas 11: Endpoint otentikasi dan ubah sandi sendiri

**Berkas:**
- Buat: `backend/app/skema/auth.py`, `backend/app/rute/auth.py`
- Modifikasi: `backend/app/main.py`, `backend/app/layanan/pengguna.py`
- Uji: `backend/tests/test_rute_auth.py`

**Antarmuka:**
- Memakai: `masuk`, `segarkan`, `keluar` (Tugas 8), `pengguna_berjalan` (Tugas 9).
- Menghasilkan: `POST /api/v1/auth/masuk`, `/auth/segarkan`, `/auth/keluar`, `GET /auth/saya`, `POST /auth/ubah-sandi`; fungsi `ubah_sandi_sendiri(sesi, pengguna, sandi_lama, sandi_baru) -> None` (AKS-04).

- [ ] **Langkah 1: Tulis `backend/app/skema/auth.py`**

```python
from pydantic import BaseModel, Field


class PermintaanMasuk(BaseModel):
    nama_pengguna: str
    sandi: str


class JawabanToken(BaseModel):
    token_akses: str
    token_segar: str


class PermintaanSegarkan(BaseModel):
    token_segar: str


class UbahSandiSendiri(BaseModel):
    sandi_lama: str
    sandi_baru: str = Field(min_length=8)
```

- [ ] **Langkah 2: Tambahkan `ubah_sandi_sendiri` ke `backend/app/layanan/pengguna.py`**

```python
from app.keamanan.sandi import verifikasi_sandi


def ubah_sandi_sendiri(sesi: Session, pengguna: Pengguna,
                       sandi_lama: str, sandi_baru: str) -> None:
    if not verifikasi_sandi(sandi_lama, pengguna.sandi_hash):
        raise KesalahanDomain(
            "SANDI_LAMA_SALAH", "Sandi lama yang Anda masukkan keliru", status=400
        )
    pengguna.sandi_hash = hash_sandi(sandi_baru)
    sesi.commit()
```

- [ ] **Langkah 3: Tulis `backend/app/rute/auth.py` dan pasang di `main.py`**

```python
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.basisdata import ambil_sesi
from app.keamanan.hak_akses import pengguna_berjalan
from app.layanan import otentikasi, pengguna as layanan_pengguna
from app.model.pengguna import Pengguna
from app.skema.auth import (
    JawabanToken, PermintaanMasuk, PermintaanSegarkan, UbahSandiSendiri,
)
from app.skema.pengguna import PenggunaKeluar

rute = APIRouter(prefix="/auth", tags=["auth"])


@rute.post("/masuk", response_model=JawabanToken)
def masuk(data: PermintaanMasuk, permintaan: Request,
          sesi: Session = Depends(ambil_sesi)) -> JawabanToken:
    ip = permintaan.client.host if permintaan.client else "tidak diketahui"
    p = otentikasi.masuk(sesi, data.nama_pengguna, data.sandi, ip)
    return JawabanToken(token_akses=p.token_akses, token_segar=p.token_segar)


@rute.post("/segarkan", response_model=JawabanToken)
def segarkan(data: PermintaanSegarkan, sesi: Session = Depends(ambil_sesi)) -> JawabanToken:
    p = otentikasi.segarkan(sesi, data.token_segar)
    return JawabanToken(token_akses=p.token_akses, token_segar=p.token_segar)


@rute.post("/keluar", status_code=204)
def keluar(data: PermintaanSegarkan, sesi: Session = Depends(ambil_sesi)) -> None:
    otentikasi.keluar(sesi, data.token_segar)


@rute.get("/saya", response_model=PenggunaKeluar)
def saya(pengguna: Pengguna = Depends(pengguna_berjalan)) -> Pengguna:
    return pengguna


@rute.post("/ubah-sandi", status_code=204)
def ubah_sandi(data: UbahSandiSendiri, sesi: Session = Depends(ambil_sesi),
               pengguna: Pengguna = Depends(pengguna_berjalan)) -> None:
    layanan_pengguna.ubah_sandi_sendiri(sesi, pengguna, data.sandi_lama, data.sandi_baru)
```

Di `main.py`: `from app.rute import auth` dan `aplikasi.include_router(auth.rute, prefix="/api/v1")`.

- [ ] **Langkah 4: Tulis uji**

```python
# tests/test_rute_auth.py
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.keamanan.sandi import hash_sandi
from app.model.pengguna import Pengguna, Peran


def _pemilik(sesi: Session) -> Pengguna:
    p = Pengguna(nama_pengguna="irvan", nama_lengkap="Irvan",
                 sandi_hash=hash_sandi("rahasia123"), peran=Peran.pemilik)
    sesi.add(p)
    sesi.commit()
    return p


def test_alur_masuk_lalu_saya(klien: TestClient, sesi: Session) -> None:
    _pemilik(sesi)
    masuk = klien.post("/api/v1/auth/masuk",
                       json={"nama_pengguna": "irvan", "sandi": "rahasia123"})
    assert masuk.status_code == 200
    token = masuk.json()["token_akses"]

    saya = klien.get("/api/v1/auth/saya", headers={"Authorization": f"Bearer {token}"})
    assert saya.status_code == 200
    assert saya.json()["nama_pengguna"] == "irvan"
    assert "sandi_hash" not in saya.json()


def test_sandi_salah_memberi_bentuk_kesalahan_seragam(klien: TestClient, sesi: Session) -> None:
    _pemilik(sesi)
    jawaban = klien.post("/api/v1/auth/masuk",
                         json={"nama_pengguna": "irvan", "sandi": "salah"})
    assert jawaban.status_code == 401
    assert set(jawaban.json()) == {"kode", "pesan", "detail"}
    assert jawaban.json()["kode"] == "KREDENSIAL_SALAH"


def test_ubah_sandi_sendiri(klien: TestClient, sesi: Session) -> None:
    _pemilik(sesi)
    token = klien.post("/api/v1/auth/masuk",
                       json={"nama_pengguna": "irvan", "sandi": "rahasia123"}
                       ).json()["token_akses"]
    ubah = klien.post("/api/v1/auth/ubah-sandi",
                      json={"sandi_lama": "rahasia123", "sandi_baru": "sandibaru456"},
                      headers={"Authorization": f"Bearer {token}"})
    assert ubah.status_code == 204
    assert klien.post("/api/v1/auth/masuk",
                      json={"nama_pengguna": "irvan", "sandi": "sandibaru456"}
                      ).status_code == 200
```

- [ ] **Langkah 5: Jalankan uji**

Jalankan: `uv run pytest tests/test_rute_auth.py -v` → 3 LULUS

- [ ] **Langkah 6: Commit**

```bash
git add backend/app/skema/auth.py backend/app/rute/auth.py backend/app/layanan/pengguna.py backend/app/main.py backend/tests/test_rute_auth.py
git commit -m "feat: endpoint otentikasi dan ubah sandi sendiri"
```

---

## Tugas 12: Perintah pembuatan pemilik pertama

**Berkas:**
- Buat: `backend/app/perintah/buat_pemilik.py`
- Uji: `backend/tests/test_buat_pemilik.py`

Tanpa ini, sistem yang baru dipasang tidak punya siapa pun yang bisa masuk, dan endpoint pembuatan pengguna menuntut pemilik yang sudah masuk. Ayam dan telur.

**Antarmuka:**
- Menghasilkan: `buat_pemilik_pertama(sesi, nama_pengguna, nama_lengkap, sandi) -> Pengguna` yang **menolak jalan bila sudah ada pengguna mana pun**.

- [ ] **Langkah 1: Tulis `backend/app/perintah/buat_pemilik.py`**

```python
import sys

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.basisdata import BuatSesi
from app.kesalahan import KesalahanDomain
from app.keamanan.sandi import hash_sandi
from app.model.pengguna import Pengguna, Peran


def buat_pemilik_pertama(sesi: Session, nama_pengguna: str,
                         nama_lengkap: str, sandi: str) -> Pengguna:
    jumlah = sesi.execute(select(func.count()).select_from(Pengguna)).scalar_one()
    if jumlah > 0:
        raise KesalahanDomain(
            "SUDAH_ADA_PENGGUNA",
            "Sistem sudah punya pengguna. Buat akun baru lewat menu Pengaturan.",
        )
    if len(sandi) < 8:
        raise KesalahanDomain("SANDI_TERLALU_PENDEK", "Sandi minimal 8 karakter")

    pemilik = Pengguna(nama_pengguna=nama_pengguna, nama_lengkap=nama_lengkap,
                       sandi_hash=hash_sandi(sandi), peran=Peran.pemilik)
    sesi.add(pemilik)
    sesi.commit()
    return pemilik


def main() -> None:
    if len(sys.argv) != 4:
        print("Pemakaian: python -m app.perintah.buat_pemilik <nama_pengguna> "
              "<nama_lengkap> <sandi>")
        raise SystemExit(1)
    with BuatSesi() as sesi:
        pemilik = buat_pemilik_pertama(sesi, sys.argv[1], sys.argv[2], sys.argv[3])
        print(f"Pemilik dibuat: {pemilik.nama_pengguna}")


if __name__ == "__main__":
    main()
```

- [ ] **Langkah 2: Tulis uji**

```python
# tests/test_buat_pemilik.py
import pytest
from sqlalchemy.orm import Session

from app.kesalahan import KesalahanDomain
from app.model.pengguna import Peran
from app.perintah.buat_pemilik import buat_pemilik_pertama


def test_membuat_pemilik_pertama(sesi: Session) -> None:
    pemilik = buat_pemilik_pertama(sesi, "irvan", "Irvan", "rahasia123")
    assert pemilik.peran is Peran.pemilik
    assert pemilik.aktif is True


def test_menolak_bila_sudah_ada_pengguna(sesi: Session) -> None:
    buat_pemilik_pertama(sesi, "irvan", "Irvan", "rahasia123")
    with pytest.raises(KesalahanDomain) as e:
        buat_pemilik_pertama(sesi, "orang2", "Orang Dua", "rahasia123")
    assert e.value.kode == "SUDAH_ADA_PENGGUNA"


def test_menolak_sandi_pendek(sesi: Session) -> None:
    with pytest.raises(KesalahanDomain) as e:
        buat_pemilik_pertama(sesi, "irvan", "Irvan", "pendek")
    assert e.value.kode == "SANDI_TERLALU_PENDEK"
```

- [ ] **Langkah 3: Jalankan uji dan coba perintahnya sungguhan**

```bash
uv run pytest tests/test_buat_pemilik.py -v
uv run python -m app.perintah.buat_pemilik irvan "Irvan" rahasia123
```

Diharapkan: 3 uji LULUS, lalu tercetak `Pemilik dibuat: irvan`

- [ ] **Langkah 4: Commit**

```bash
git add backend/app/perintah backend/tests/test_buat_pemilik.py
git commit -m "feat: perintah pembuatan pemilik pertama"
```

---

## Tugas 13: Kerangka frontend dan klien HTTP

**Berkas:**
- Buat: `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/tailwind.config.js`, `frontend/index.html`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/api/klien.ts`
- Uji: `frontend/tests/klien.test.ts`

**Antarmuka:**
- Menghasilkan: `klien.minta<T>(jalur: string, opsi?: OpsiMinta): Promise<T>`, `simpanToken(akses: string, segar: string): void`, `hapusToken(): void`, `ambilTokenAkses(): string | null`, kelas `KesalahanApi` dengan `kode`, `pesan`, `status`.

- [ ] **Langkah 1: Buat proyek dan pasang dependensi**

```bash
cd frontend
npm create vite@latest. -- --template react-ts
npm install
npm install -D tailwindcss @tailwindcss/postcss postcss autoprefixer vitest jsdom @testing-library/react
npx tailwindcss init
```

- [ ] **Langkah 2: Tulis `frontend/src/api/klien.ts`**

```typescript
const DASAR = import.meta.env.VITE_API_DASAR ?? "http://localhost:8000/api/v1";

const KUNCI_AKSES = "toko.token_akses";
const KUNCI_SEGAR = "toko.token_segar";

export class KesalahanApi extends Error {
  constructor(
    readonly kode: string,
    readonly pesan: string,
    readonly status: number,
  ) {
    super(pesan);
  }
}

export function simpanToken(akses: string, segar: string): void {
  localStorage.setItem(KUNCI_AKSES, akses);
  localStorage.setItem(KUNCI_SEGAR, segar);
}

export function hapusToken(): void {
  localStorage.removeItem(KUNCI_AKSES);
  localStorage.removeItem(KUNCI_SEGAR);
}

export function ambilTokenAkses(): string | null {
  return localStorage.getItem(KUNCI_AKSES);
}

interface OpsiMinta {
  metode?: "GET" | "POST" | "PATCH";
  muatan?: unknown;
}

export async function minta<T>(jalur: string, opsi: OpsiMinta = {}): Promise<T> {
  const token = ambilTokenAkses();
  const jawaban = await fetch(`${DASAR}${jalur}`, {
    method: opsi.metode ?? "GET",
    headers: {
      "Content-Type": "application/json",
...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: opsi.muatan === undefined ? undefined : JSON.stringify(opsi.muatan),
  });

  if (jawaban.status === 204) return undefined as T;

  if (!jawaban.ok) {
    const isi = await jawaban.json().catch(() => null);
    throw new KesalahanApi(
      isi?.kode ?? "KESALAHAN_TIDAK_DIKENAL",
      isi?.pesan ?? "Terjadi kesalahan sistem. Coba lagi sebentar lagi.",
      jawaban.status,
    );
  }
  return (await jawaban.json()) as T;
}
```

Pesan dari server ditampilkan apa adanya, tidak diterjemahkan ulang ([07 §7.1](../perancangan/07-kontrak-api.md)).

- [ ] **Langkah 3: Tulis uji**

```typescript
// tests/klien.test.ts
import { beforeEach, describe, expect, it, vi } from "vitest";
import { KesalahanApi, ambilTokenAkses, hapusToken, minta, simpanToken } from "../src/api/klien";

describe("klien api", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("menyimpan dan menghapus token", () => {
    simpanToken("a", "s");
    expect(ambilTokenAkses()).toBe("a");
    hapusToken();
    expect(ambilTokenAkses()).toBeNull();
  });

  it("menyisipkan token ke kepala permintaan", async () => {
    simpanToken("token-uji", "s");
    const tiruan = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), { status: 200 }),
    );
    vi.stubGlobal("fetch", tiruan);
    await minta("/auth/saya");
    expect(tiruan.mock.calls[0][1].headers.Authorization).toBe("Bearer token-uji");
  });

  it("mengubah jawaban kesalahan menjadi KesalahanApi", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ kode: "KREDENSIAL_SALAH", pesan: "Nama pengguna atau sandi keliru" }),
        { status: 401 },
      ),
    ));
    await expect(minta("/auth/masuk", { metode: "POST", muatan: {} }))
.rejects.toMatchObject({ kode: "KREDENSIAL_SALAH", status: 401 });
  });

  it("menampilkan pesan server apa adanya", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ kode: "X", pesan: "Pesan khusus dari server" }),
        { status: 422 }),
    ));
    try {
      await minta("/apa-pun");
      expect.unreachable();
    } catch (e) {
      expect((e as KesalahanApi).pesan).toBe("Pesan khusus dari server");
    }
  });
});
```

- [ ] **Langkah 4: Jalankan uji**

Jalankan: `npx vitest run` → 4 LULUS

- [ ] **Langkah 5: Commit**

```bash
git add frontend
git commit -m "feat: kerangka frontend dan klien HTTP"
```

---

## Tugas 14: Pembangkitan tipe TypeScript dari OpenAPI

**Berkas:**
- Buat: `frontend/src/api/tipe.ts` (dibangkitkan), `backend/skrip/ekspor_openapi.py`
- Modifikasi: `frontend/package.json`

**Antarmuka:**
- Menghasilkan: `frontend/src/api/tipe.ts` berisi tipe untuk seluruh endpoint. **Berkas ini tidak pernah disunting tangan.**

- [ ] **Langkah 1: Tulis `backend/skrip/ekspor_openapi.py`**

```python
import json
from pathlib import Path

from app.main import buat_aplikasi


def main() -> None:
    berkas = Path(__file__).parent.parent / "openapi.json"
    berkas.write_text(json.dumps(buat_aplikasi().openapi(), indent=2), encoding="utf-8")
    print(f"OpenAPI ditulis ke {berkas}")


if __name__ == "__main__":
    main()
```

- [ ] **Langkah 2: Tambahkan skrip ke `frontend/package.json`**

```json
{
  "scripts": {
    "tipe": "cd../backend && uv run python -m skrip.ekspor_openapi && cd../frontend && npx openapi-typescript../backend/openapi.json -o src/api/tipe.ts"
  }
}
```

Pasang: `npm install -D openapi-typescript`

- [ ] **Langkah 3: Bangkitkan dan periksa hasilnya**

```bash
cd frontend && npm run tipe
head -30 src/api/tipe.ts
```

Diharapkan: berkas memuat definisi jalur `/auth/masuk`, `/pengguna`, dan skema `PenggunaKeluar`.

- [ ] **Langkah 4: Tambahkan penanda jangan-disunting**

Sisipkan di baris pertama `frontend/src/api/tipe.ts` (dan pastikan skrip menambahkannya ulang setiap kali dibangkitkan):

```typescript
// BERKAS INI DIBANGKITKAN OTOMATIS DARI OpenAPI. JANGAN DISUNTING TANGAN.
// Bangkitkan ulang dengan: npm run tipe
```

- [ ] **Langkah 5: Commit**

```bash
git add backend/skrip frontend/package.json frontend/src/api/tipe.ts
git commit -m "feat: bangkitkan tipe TypeScript dari OpenAPI"
```

---

## Tugas 15: Layar masuk

**Berkas:**
- Buat: `frontend/src/fitur/masuk/LayarMasuk.tsx`, `frontend/src/komponen/Tombol.tsx`, `frontend/src/komponen/Kolom.tsx`, `frontend/src/komponen/PesanKesalahan.tsx`
- Modifikasi: `frontend/src/App.tsx`
- Uji: `frontend/tests/LayarMasuk.test.tsx`

**Antarmuka:**
- Memakai: `minta`, `simpanToken`, `KesalahanApi` (Tugas 13).
- Menghasilkan: komponen `LayarMasuk` dengan properti `{ onBerhasil: () => void }`.

- [ ] **Langkah 1: Tulis `frontend/src/fitur/masuk/LayarMasuk.tsx`**

```tsx
import { useState } from "react";
import { KesalahanApi, minta, simpanToken } from "../../api/klien";

interface JawabanToken {
  token_akses: string;
  token_segar: string;
}

export function LayarMasuk({ onBerhasil }: { onBerhasil: () => void }) {
  const [namaPengguna, setNamaPengguna] = useState("");
  const [sandi, setSandi] = useState("");
  const [kesalahan, setKesalahan] = useState<string | null>(null);
  const [sedangKirim, setSedangKirim] = useState(false);

  async function kirim(e: React.FormEvent) {
    e.preventDefault();
    setKesalahan(null);
    setSedangKirim(true);
    try {
      const jawaban = await minta<JawabanToken>("/auth/masuk", {
        metode: "POST",
        muatan: { nama_pengguna: namaPengguna, sandi },
      });
      simpanToken(jawaban.token_akses, jawaban.token_segar);
      onBerhasil();
    } catch (e) {
      setKesalahan(e instanceof KesalahanApi ? e.pesan : "Tidak bisa terhubung ke server");
    } finally {
      setSedangKirim(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-white p-4">
      <form onSubmit={kirim} className="w-full max-w-sm space-y-4">
        <h1 className="text-2xl font-bold text-gray-900">Masuk</h1>

        <label className="block">
          <span className="text-sm font-medium text-gray-900">Nama pengguna</span>
          <input
            autoFocus
            value={namaPengguna}
            onChange={(e) => setNamaPengguna(e.target.value)}
            className="mt-1 w-full rounded border border-gray-400 px-3 py-2 text-gray-900"
          />
        </label>

        <label className="block">
          <span className="text-sm font-medium text-gray-900">Sandi</span>
          <input
            type="password"
            value={sandi}
            onChange={(e) => setSandi(e.target.value)}
            className="mt-1 w-full rounded border border-gray-400 px-3 py-2 text-gray-900"
          />
        </label>

        {kesalahan && (
          <p role="alert" className="text-sm text-red-700">{kesalahan}</p>
        )}

        <button
          type="submit"
          disabled={sedangKirim}
          className="w-full rounded bg-gray-900 px-4 py-3 text-white disabled:opacity-50"
        >
          {sedangKirim ? "Memproses..." : "Masuk"}
        </button>
      </form>
    </main>
  );
}
```

Warna teks memakai `gray-900` di atas putih untuk memenuhi syarat kontras ([06 §6.6](../perancangan/06-antarmuka.md)). Tinggi tombol 3rem agar nyaman disentuh di HP (NF-07).

- [ ] **Langkah 2: Tulis uji**

```tsx
// tests/LayarMasuk.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { LayarMasuk } from "../src/fitur/masuk/LayarMasuk";

describe("LayarMasuk", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("menyimpan token dan memanggil onBerhasil saat masuk berhasil", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ token_akses: "a", token_segar: "s" }), { status: 200 }),
    ));
    const onBerhasil = vi.fn();
    render(<LayarMasuk onBerhasil={onBerhasil} />);

    await userEvent.type(screen.getByLabelText("Nama pengguna"), "irvan");
    await userEvent.type(screen.getByLabelText("Sandi"), "rahasia123");
    await userEvent.click(screen.getByRole("button", { name: "Masuk" }));

    expect(onBerhasil).toHaveBeenCalled();
    expect(localStorage.getItem("toko.token_akses")).toBe("a");
  });

  it("menampilkan pesan server saat kredensial salah", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ kode: "KREDENSIAL_SALAH", pesan: "Nama pengguna atau sandi keliru" }),
        { status: 401 },
      ),
    ));
    render(<LayarMasuk onBerhasil={vi.fn()} />);

    await userEvent.type(screen.getByLabelText("Nama pengguna"), "irvan");
    await userEvent.type(screen.getByLabelText("Sandi"), "salah");
    await userEvent.click(screen.getByRole("button", { name: "Masuk" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Nama pengguna atau sandi keliru");
  });
});
```

- [ ] **Langkah 3: Jalankan uji**

Jalankan: `npx vitest run` → seluruh uji LULUS

- [ ] **Langkah 4: Commit**

```bash
git add frontend/src frontend/tests
git commit -m "feat: layar masuk"
```

---

## Tugas 16: Layar pengelolaan pengguna

**Berkas:**
- Buat: `frontend/src/fitur/pengguna/LayarPengguna.tsx`
- Modifikasi: `frontend/src/App.tsx`
- Uji: `frontend/tests/LayarPengguna.test.tsx`

**Antarmuka:**
- Memakai: `minta`, `KesalahanApi` (Tugas 13); endpoint `/pengguna` (Tugas 10).
- Menghasilkan: komponen `LayarPengguna` tanpa properti.

- [ ] **Langkah 1: Tulis `frontend/src/fitur/pengguna/LayarPengguna.tsx`**

```tsx
import { useEffect, useState } from "react";
import { KesalahanApi, minta } from "../../api/klien";

interface Pengguna {
  id: number;
  nama_pengguna: string;
  nama_lengkap: string;
  peran: "pemilik" | "kasir";
  aktif: boolean;
}

export function LayarPengguna() {
  const [daftar, setDaftar] = useState<Pengguna[]>([]);
  const [kesalahan, setKesalahan] = useState<string | null>(null);

  async function muat() {
    try {
      setDaftar(await minta<Pengguna[]>("/pengguna"));
    } catch (e) {
      setKesalahan(e instanceof KesalahanApi ? e.pesan : "Tidak bisa terhubung ke server");
    }
  }

  useEffect(() => { void muat(); }, []);

  async function ubahAktif(p: Pengguna) {
    setKesalahan(null);
    try {
      await minta(`/pengguna/${p.id}`, { metode: "PATCH", muatan: { aktif: !p.aktif } });
      await muat();
    } catch (e) {
      setKesalahan(e instanceof KesalahanApi ? e.pesan : "Tidak bisa terhubung ke server");
    }
  }

  return (
    <section className="p-4 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Pengguna</h1>

      {kesalahan && <p role="alert" className="mb-4 text-sm text-red-700">{kesalahan}</p>}

      <ul className="space-y-2">
        {daftar.map((p) => (
          <li key={p.id} className="flex items-center justify-between gap-3 rounded
                                    border border-gray-300 p-3">
            <div>
              <p className="font-medium text-gray-900">{p.nama_lengkap}</p>
              <p className="text-sm text-gray-700">
                {p.nama_pengguna} · {p.peran}{!p.aktif && " · nonaktif"}
              </p>
            </div>
            <button
              onClick={() => void ubahAktif(p)}
              className="rounded border border-gray-400 px-3 py-2 text-gray-900"
            >
              {p.aktif ? "Nonaktifkan" : "Aktifkan"}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
```

- [ ] **Langkah 2: Tulis uji**

```tsx
// tests/LayarPengguna.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { LayarPengguna } from "../src/fitur/pengguna/LayarPengguna";

const DAFTAR = [
  { id: 1, nama_pengguna: "irvan", nama_lengkap: "Irvan", peran: "pemilik", aktif: true },
];

describe("LayarPengguna", () => {
  beforeEach(() => { localStorage.clear(); vi.restoreAllMocks(); });

  it("menampilkan daftar pengguna", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(JSON.stringify(DAFTAR), { status: 200 }),
    ));
    render(<LayarPengguna />);
    expect(await screen.findByText("Irvan")).toBeDefined();
  });

  it("menampilkan pesan server saat menonaktifkan pemilik terakhir", async () => {
    const tiruan = vi.fn()
.mockResolvedValueOnce(new Response(JSON.stringify(DAFTAR), { status: 200 }))
.mockResolvedValueOnce(new Response(
        JSON.stringify({
          kode: "PEMILIK_TERAKHIR",
          pesan: "Tindakan ini menyisakan nol akun pemilik aktif. Tunjuk pemilik lain lebih dulu.",
        }),
        { status: 422 },
      ));
    vi.stubGlobal("fetch", tiruan);

    render(<LayarPengguna />);
    await userEvent.click(await screen.findByRole("button", { name: "Nonaktifkan" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("nol akun pemilik aktif");
  });
});
```

- [ ] **Langkah 3: Jalankan uji**

Jalankan: `npx vitest run` → seluruh uji LULUS

- [ ] **Langkah 4: Jalankan seluruhnya sungguhan**

```bash
cd backend && uv run python -m skrip.nyalakan_basisdata
uv run alembic upgrade head && uv run uvicorn app.main:app --reload &
cd frontend && npm run dev
```

Buka `http://localhost:5173`, masuk dengan akun dari Tugas 12, dan pastikan daftar pengguna tampil.

- [ ] **Langkah 5: Commit**

```bash
git add frontend/src frontend/tests
git commit -m "feat: layar pengelolaan pengguna"
```

---

## Tugas 17: Alur CI dan gerbang uji

**Berkas:**
- Buat: `.github/workflows/uji.yml`, `.github/skrip/periksa_uji.sh`

**Antarmuka:**
- Menghasilkan: alur CI yang gagal bila `backend/app/layanan/` berubah tanpa perubahan di `backend/tests/`.

- [ ] **Langkah 1: Tulis `.github/skrip/periksa_uji.sh`**

```bash
#!/usr/bin/env bash
# Gerbang pengganti disiplin uji-dulu (bab 10 §10.2).
set -euo pipefail

dasar="${1:-origin/main}"
berubah=$(git diff --name-only "$dasar"...HEAD)

layanan=$(echo "$berubah" | grep '^backend/app/layanan/' || true)
uji=$(echo "$berubah" | grep '^backend/tests/' || true)

if [[ -n "$layanan" && -z "$uji" ]]; then
  echo "GAGAL: aturan bisnis berubah tanpa uji yang menyertainya."
  echo "Berkas layanan yang berubah:"
  echo "$layanan" | sed 's/^/  /'
  echo "Tambahkan atau perbarui uji di backend/tests/ sebelum menggabungkan."
  exit 1
fi

echo "OK: tidak ada perubahan aturan bisnis yang tanpa uji."
```

Jadikan bisa dijalankan: `chmod +x.github/skrip/periksa_uji.sh`

- [ ] **Langkah 2: Tulis `.github/workflows/uji.yml`**

```yaml
name: uji

on:
  push:
    branches: [main]
  pull_request:

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: astral-sh/setup-uv@v4
      - run: uv python install 3.12
      - name: Gerbang uji
        if: github.event_name == 'pull_request'
        run:./.github/skrip/periksa_uji.sh origin/${{ github.base_ref }}
      - working-directory: backend
        run: |
          uv sync --all-groups
          uv run ruff check.
          uv run mypy app
          uv run pytest -v
          uv run pip-audit

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "22" }
      - working-directory: frontend
        run: |
          npm ci
          npx tsc --noEmit
          npx vitest run
          npm audit --audit-level=high
```

Seluruh langkah memakai Actions gratis. Untuk repositori privat, kuota gratisnya 2.000 menit per bulan, jauh di atas kebutuhan proyek ini (G1).

- [ ] **Langkah 3: Uji gerbangnya secara lokal**

```bash
# Harus GAGAL: ubah layanan tanpa uji
echo "# coba" >> backend/app/layanan/pengguna.py
git add -A && git commit -m "coba: layanan tanpa uji"
./.github/skrip/periksa_uji.sh HEAD~1
```

Diharapkan: keluar dengan kode 1 dan pesan `GAGAL: aturan bisnis berubah tanpa uji`.

Lalu batalkan: `git reset --hard HEAD~1`

- [ ] **Langkah 4: Commit**

```bash
git add.github
git commit -m "ci: alur uji dan gerbang perubahan aturan bisnis"
```

---

## Tugas 18: Pemeriksaan M0 dari ujung ke ujung di localhost

Tugas terakhir M0. Tidak menulis kode baru; memastikan seluruh bagian bekerja bersama.

- [ ] **Langkah 1: Nyalakan semuanya dari keadaan bersih**

```bash
rm -rf backend/data_pg          # buang data lama agar benar-benar dari nol
cd backend && uv run python -m skrip.nyalakan_basisdata
uv run alembic upgrade head
uv run python -m app.perintah.buat_pemilik irvan "Irvan" rahasia123
uv run uvicorn app.main:app --reload &
cd../frontend && npm run dev
```

- [ ] **Langkah 2: Telusuri alur pemilik**

1. Buka `http://localhost:5173`, masuk sebagai `irvan`.
2. Buka layar Pengguna, buat akun kasir baru.
3. Coba nonaktifkan akun `irvan` sendiri → harus ditolak dengan pesan tentang **nol akun pemilik aktif** (AKS-05).
4. Ubah sandi sendiri, keluar, lalu masuk dengan sandi baru (AKS-04).

- [ ] **Langkah 3: Telusuri alur kasir**

1. Keluar, masuk sebagai kasir yang barusan dibuat.
2. Pastikan layar Pengguna **tidak bisa dibuka** dan pesannya menyebut peran tidak mengizinkan.
3. Buka `http://localhost:8000/api/v1/pengguna` langsung dengan token kasir → harus `403`.

Langkah 3 penting: ia membuktikan penjagaan ada di server, bukan sekadar menu yang disembunyikan ([08 §8.1](../perancangan/08-keamanan-dan-peran.md)).

- [ ] **Langkah 4: Jalankan seluruh uji dan pemeriksa**

```bash
cd backend && uv run ruff check. && uv run mypy app && uv run pytest -v
cd../frontend && npx tsc --noEmit && npx vitest run
```

Diharapkan: seluruhnya lulus, tanpa peringatan tipe.

- [ ] **Langkah 5: Commit**

```bash
git add -A
git commit -m "chore: M0 selesai, terverifikasi dari ujung ke ujung di localhost"
```

**M0 selesai** ketika kelima langkah ini lulus.

---

## Tugas Tertunda: Penempatan ke lapisan gratis

> **Ditunda atas keputusan pemilik proyek (2026-08-08).** M0 dinyatakan selesai tanpa tugas ini. Kerjakan ketika kebutuhan "pemilik memantau dari HP di mana saja" mulai mendesak, paling lambat sebelum M3, karena semakin banyak bagian yang sudah jadi, semakin sulit mencari tahu penyebab kegagalan penempatan.

**Prasyarat:** daftar akun Neon dan Render lebih dulu, dengan aturan **berhenti seketika bila diminta data pembayaran** (G1). Catat hasilnya di `docs/rencana/catatan-penempatan.md`: nama layanan, tanggal diperiksa, apakah meminta kartu, dan batas kuota gratis yang tertulis.

**Berkas:**
- Buat: `backend/Dockerfile`, `render.yaml`, `docs/rencana/catatan-penempatan.md` (diperbarui)

- [ ] **Langkah 1: Tulis `backend/Dockerfile`**

```dockerfile
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock./
RUN uv sync --frozen --no-dev

COPY..

CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

- [ ] **Langkah 2: Siapkan basis data dan tempatkan API**

1. Buat proyek PostgreSQL di Neon, salin URL sambungannya.
2. Di Render, buat Web Service dari repositori ini, tipe **Free**, akar `backend/`.
3. Isi variabel lingkungan: `DATABASE_URL` (dari Neon), `RAHASIA_JWT` (hasil `openssl rand -hex 32`), `ASAL_FRONTEND` (URL Cloudflare Pages dari Langkah 3).

> **Bila di titik mana pun diminta data pembayaran, berhenti.** Catat di `catatan-penempatan.md` dan laporkan sebelum melanjutkan (G1).

- [ ] **Langkah 3: Tempatkan frontend**

Di Cloudflare Pages, hubungkan repositori, direktori akar `frontend/`, perintah bangun `npm run build`, direktori keluaran `dist`, variabel `VITE_API_DASAR` berisi URL Render ditambah `/api/v1`.

- [ ] **Langkah 4: Buat pemilik pertama di lingkungan sungguhan**

Lewat Render Shell:

```bash
uv run python -m app.perintah.buat_pemilik irvan "Irvan" <sandi-kuat>
```

- [ ] **Langkah 5: Pastikan hidup dari ujung ke ujung**

1. Buka URL Cloudflare Pages, masuk dengan akun tadi.
2. Buat satu akun kasir lewat layar Pengguna.
3. Keluar, masuk sebagai kasir, pastikan layar Pengguna **ditolak**.
4. Buka URL Render `/api/v1/sehat`, pastikan menjawab `{"status":"sehat"}`.

Tugas ini **bukan** syarat selesainya M0. Ia menutup satu kebutuhan yang berdiri sendiri: sistem bisa dibuka dari luar komputer tempat ia dijalankan.

- [ ] **Langkah 6: Perbarui catatan dan commit**

Tambahkan ke `docs/rencana/catatan-penempatan.md`: URL yang dipakai, tanggal penempatan, dan **konfirmasi tertulis bahwa tidak ada biaya yang timbul**.

```bash
git add backend/Dockerfile render.yaml docs/rencana/catatan-penempatan.md
git commit -m "chore: penempatan ke lapisan gratis"
```

---

## Setelah M0

M1 (Katalog) disusun sebagai rencana tersendiri setelah M0 selesai, memakai apa yang dipelajari di sini. Dua hal dari M0 yang perlu dibawa ke M1:

- Pola `rute → layanan → model` sudah terbentuk; M1 mengikutinya tanpa menemukan pola baru.
- Penjagaan `SESI_KAS_MASIH_TERBUKA` masih menunggu tabel `sesi_kas` di M2. Catat sebagai hutang yang sudah dijadwalkan, bukan yang terlupakan.
