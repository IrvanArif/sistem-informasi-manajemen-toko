from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.basisdata import ambil_sesi
from app.keamanan.hak_akses import pengguna_berjalan
from app.layanan import kas as layanan_kas
from app.layanan import penjualan as layanan
from app.model.pengguna import Pengguna
from app.skema.penjualan import (
    BukaSesi,
    PenjualanKeluar,
    PenjualanMasuk,
    SesiKasKeluar,
    TutupSesi,
)

rute = APIRouter(tags=["kasir"])


@rute.post("/sesi-kas", status_code=201, response_model=SesiKasKeluar)
def buka_sesi(
    data: BukaSesi,
    sesi: Session = Depends(ambil_sesi),
    pengguna: Pengguna = Depends(pengguna_berjalan),
) -> Any:
    return layanan_kas.buka_sesi(sesi, pengguna.id, data.modal_awal)


@rute.get("/sesi-kas/aktif", response_model=SesiKasKeluar | None)
def sesi_aktif(
    sesi: Session = Depends(ambil_sesi),
    pengguna: Pengguna = Depends(pengguna_berjalan),
) -> Any:
    return layanan_kas.sesi_aktif(sesi, pengguna.id)


@rute.get("/sesi-kas/{kas_id}/kas-sistem")
def kas_sistem(
    kas_id: int,
    sesi: Session = Depends(ambil_sesi),
    pengguna: Pengguna = Depends(pengguna_berjalan),
) -> dict[str, int]:
    """Kas yang seharusnya ada di laci, untuk dibandingkan saat menutup."""
    kas = layanan_kas.sesi_aktif(sesi, pengguna.id)
    if kas is None or kas.id != kas_id:
        return {"kas_sistem": 0}
    return {"kas_sistem": layanan_kas.hitung_kas_sistem(sesi, kas)}


@rute.post("/sesi-kas/{kas_id}/tutup", response_model=SesiKasKeluar)
def tutup_sesi(
    kas_id: int,
    data: TutupSesi,
    sesi: Session = Depends(ambil_sesi),
    pengguna: Pengguna = Depends(pengguna_berjalan),
) -> Any:
    return layanan_kas.tutup_sesi(
        sesi, kas_id, data.kas_fisik, data.catatan, pengguna.id
    )


@rute.post("/penjualan", response_model=PenjualanKeluar)
def catat_penjualan(
    data: PenjualanMasuk,
    jawaban: Response,
    sesi: Session = Depends(ambil_sesi),
    pengguna: Pengguna = Depends(pengguna_berjalan),
) -> Any:
    """201 bila baru disimpan, 200 bila UUID-nya sudah pernah masuk.

    Perbedaan kode itu penting bagi perangkat: 200 berarti pengiriman
    ulang berhasil dikenali, bukan bahwa notanya tercatat dua kali.
    """
    nota, baru = layanan.catat_penjualan(sesi, data, pengguna.id)
    jawaban.status_code = 201 if baru else 200
    return nota


@rute.get("/penjualan", response_model=list[PenjualanKeluar])
def daftar_penjualan(
    dari: datetime | None = None,
    sampai: datetime | None = None,
    batas: int = Query(default=100, le=500),
    sesi: Session = Depends(ambil_sesi),
    _: Pengguna = Depends(pengguna_berjalan),
) -> Any:
    return layanan.daftar_penjualan(sesi, dari, sampai, batas)
