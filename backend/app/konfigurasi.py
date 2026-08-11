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

    Bila DATABASE_URL diisi, itu yang dipakai. Jalur untuk penempatan.
    Bila kosong, PostgreSQL tersemat dinyalakan. Jalur untuk pengembangan.
    """
    if ditetapkan := ambil_pengaturan().database_url:
        return ditetapkan

    # Diimpor di dalam fungsi supaya pgserver tidak ikut dimuat di server
    # sungguhan, tempat DATABASE_URL selalu terisi.
    from skrip.nyalakan_basisdata import uri_sqlalchemy

    return uri_sqlalchemy()
