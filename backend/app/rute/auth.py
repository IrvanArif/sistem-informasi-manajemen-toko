from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.basisdata import ambil_sesi
from app.keamanan.hak_akses import pengguna_berjalan
from app.layanan import otentikasi
from app.layanan import pengguna as layanan_pengguna
from app.model.pengguna import Pengguna
from app.skema.auth import (
    JawabanToken,
    PermintaanMasuk,
    PermintaanSegarkan,
    UbahSandiSendiri,
)
from app.skema.pengguna import PenggunaKeluar

rute = APIRouter(prefix="/auth", tags=["auth"])


@rute.post("/masuk", response_model=JawabanToken)
def masuk(
    data: PermintaanMasuk,
    permintaan: Request,
    sesi: Session = Depends(ambil_sesi),
) -> JawabanToken:
    ip = permintaan.client.host if permintaan.client else "tidak diketahui"
    p = otentikasi.masuk(sesi, data.nama_pengguna, data.sandi, ip)
    return JawabanToken(token_akses=p.token_akses, token_segar=p.token_segar)


@rute.post("/segarkan", response_model=JawabanToken)
def segarkan(
    data: PermintaanSegarkan, sesi: Session = Depends(ambil_sesi)
) -> JawabanToken:
    p = otentikasi.segarkan(sesi, data.token_segar)
    return JawabanToken(token_akses=p.token_akses, token_segar=p.token_segar)


@rute.post("/keluar", status_code=204)
def keluar(data: PermintaanSegarkan, sesi: Session = Depends(ambil_sesi)) -> None:
    otentikasi.keluar(sesi, data.token_segar)


@rute.get("/saya", response_model=PenggunaKeluar)
def saya(pengguna: Pengguna = Depends(pengguna_berjalan)) -> Pengguna:
    return pengguna


@rute.post("/ubah-sandi", status_code=204)
def ubah_sandi(
    data: UbahSandiSendiri,
    sesi: Session = Depends(ambil_sesi),
    pengguna: Pengguna = Depends(pengguna_berjalan),
) -> None:
    layanan_pengguna.ubah_sandi_sendiri(
        sesi, pengguna, data.sandi_lama, data.sandi_baru
    )
