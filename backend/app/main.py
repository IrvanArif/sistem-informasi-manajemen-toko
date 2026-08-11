from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.kesalahan import KesalahanDomain
from app.konfigurasi import ambil_pengaturan
from app.rute import auth, pengguna, sehat


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
    @aplikasi.exception_handler(KesalahanDomain)
    async def tangani_kesalahan_domain(
        _: Request, e: KesalahanDomain
    ) -> JSONResponse:
        return JSONResponse(status_code=e.status, content=e.sebagai_jawaban())

    for r in (sehat.rute, auth.rute, pengguna.rute):
        aplikasi.include_router(r, prefix="/api/v1")
    return aplikasi


app = buat_aplikasi()
