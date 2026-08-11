from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.basisdata import ambil_sesi
from app.keamanan.hak_akses import wajib_pemilik
from app.layanan import pengguna as layanan
from app.model.pengguna import Pengguna
from app.skema.pengguna import AturUlangSandi, BuatPengguna, PenggunaKeluar, UbahPengguna

rute = APIRouter(prefix="/pengguna", tags=["pengguna"])


@rute.get("", response_model=list[PenggunaKeluar])
def daftar(
    sesi: Session = Depends(ambil_sesi),
    _: Pengguna = Depends(wajib_pemilik),
) -> list[Pengguna]:
    return layanan.daftar_pengguna(sesi)


@rute.post("", response_model=PenggunaKeluar, status_code=201)
def buat(
    data: BuatPengguna,
    sesi: Session = Depends(ambil_sesi),
    _: Pengguna = Depends(wajib_pemilik),
) -> Pengguna:
    return layanan.buat_pengguna(sesi, data)


@rute.patch("/{pengguna_id}", response_model=PenggunaKeluar)
def ubah(
    pengguna_id: int,
    data: UbahPengguna,
    sesi: Session = Depends(ambil_sesi),
    oleh: Pengguna = Depends(wajib_pemilik),
) -> Pengguna:
    return layanan.ubah_pengguna(sesi, pengguna_id, data, oleh)


@rute.post("/{pengguna_id}/atur-ulang-sandi", status_code=204)
def atur_ulang(
    pengguna_id: int,
    data: AturUlangSandi,
    sesi: Session = Depends(ambil_sesi),
    _: Pengguna = Depends(wajib_pemilik),
) -> None:
    layanan.atur_ulang_sandi(sesi, pengguna_id, data.sandi_baru)
