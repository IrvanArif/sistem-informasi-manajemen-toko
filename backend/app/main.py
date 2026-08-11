from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.konfigurasi import ambil_pengaturan
from app.rute import sehat


def buat_aplikasi() -> FastAPI:
    produksi = ambil_pengaturan().lingkungan == "produksi"
    aplikasi = FastAPI(
        title="Sistem Informasi Manajemen Toko",
        version="0.1.0",
        # Di produksi, peta endpoint tidak disajikan ke publik. Ini bukan
        # pengamanan lewat kerahasiaan: endpoint tetap bisa ditemukan
        # dengan usaha. Yang dihapus hanyalah daftar siap pakai yang
        # memudahkan penjelajahan otomatis.
        docs_url=None if produksi else "/docs",
        redoc_url=None,
        openapi_url=None if produksi else "/openapi.json",
    )
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
