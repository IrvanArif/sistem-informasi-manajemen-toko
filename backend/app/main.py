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
