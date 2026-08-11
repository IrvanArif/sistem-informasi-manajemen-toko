import pytest

from app.konfigurasi import ambil_pengaturan
from app.main import buat_aplikasi


@pytest.fixture
def bersihkan_pengaturan() -> None:
    ambil_pengaturan.cache_clear()


def test_dokumentasi_terbuka_saat_pengembangan(
    monkeypatch: pytest.MonkeyPatch, bersihkan_pengaturan: None
) -> None:
    monkeypatch.setenv("LINGKUNGAN", "pengembangan")
    ambil_pengaturan.cache_clear()
    aplikasi = buat_aplikasi()
    assert aplikasi.docs_url == "/docs"
    assert aplikasi.openapi_url == "/openapi.json"
    ambil_pengaturan.cache_clear()


def test_dokumentasi_tertutup_saat_produksi(
    monkeypatch: pytest.MonkeyPatch, bersihkan_pengaturan: None
) -> None:
    monkeypatch.setenv("LINGKUNGAN", "produksi")
    ambil_pengaturan.cache_clear()
    aplikasi = buat_aplikasi()
    assert aplikasi.docs_url is None
    assert aplikasi.openapi_url is None
    ambil_pengaturan.cache_clear()


def test_cors_tidak_pernah_mengizinkan_semua_asal() -> None:
    ambil_pengaturan.cache_clear()
    aplikasi = buat_aplikasi()
    asal: list[str] = []
    for lapis in aplikasi.user_middleware:
        nilai = lapis.kwargs.get("allow_origins")
        if isinstance(nilai, list):
            asal.extend(str(a) for a in nilai)
    assert asal, "CORS harus menyebut asal secara tegas"
    assert "*" not in asal
