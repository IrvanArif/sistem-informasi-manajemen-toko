from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.basisdata import ambil_sesi
from app.keamanan.hak_akses import pengguna_berjalan, wajib_pemilik
from app.layanan import produk as layanan
from app.layanan import stok as layanan_stok
from app.model.pengguna import Pengguna, Peran
from app.model.produk import Produk
from app.skema.produk import (
    KategoriKeluar,
    KategoriMasuk,
    MutasiKeluar,
    PenyesuaianStok,
    ProdukKeluar,
    ProdukKeluarKasir,
    ProdukKilat,
    ProdukMasuk,
    ProdukUbah,
    SatuanKeluar,
    SatuanMasuk,
)

rute = APIRouter(tags=["katalog"])


def _sesuai_peran(produk: Produk | list[Produk], pengguna: Pengguna) -> Any:
    """Menyaring kolom hpp untuk peran kasir.

    Penyaringan dilakukan di sini, sebelum data meninggalkan server, bukan
    dengan menyembunyikannya di tampilan. Kolom yang tidak pernah dikirim
    tidak bisa dibaca dari alat pengembang browser (bab 08 §8.1).
    """
    bentuk = ProdukKeluar if pengguna.peran is Peran.pemilik else ProdukKeluarKasir
    if isinstance(produk, list):
        return [bentuk.model_validate(p) for p in produk]
    return bentuk.model_validate(produk)


@rute.get("/produk")
def daftar_produk(
    cari: str = "",
    kategori_id: int | None = None,
    aktif: bool | None = True,
    perlu_dilengkapi: bool | None = None,
    batas: int = Query(default=50, le=200),
    sesi: Session = Depends(ambil_sesi),
    pengguna: Pengguna = Depends(pengguna_berjalan),
) -> Any:
    hasil = layanan.cari_produk(sesi, cari, kategori_id, aktif, perlu_dilengkapi, batas)
    return _sesuai_peran(hasil, pengguna)


@rute.get("/produk/{produk_id}")
def satu_produk(
    produk_id: int,
    sesi: Session = Depends(ambil_sesi),
    pengguna: Pengguna = Depends(pengguna_berjalan),
) -> Any:
    return _sesuai_peran(layanan.ambil_produk(sesi, produk_id), pengguna)


@rute.post("/produk", status_code=201)
def buat_produk(
    data: ProdukMasuk,
    sesi: Session = Depends(ambil_sesi),
    pemilik: Pengguna = Depends(wajib_pemilik),
) -> ProdukKeluar:
    return ProdukKeluar.model_validate(layanan.buat_produk(sesi, data, pemilik.id))


@rute.patch("/produk/{produk_id}")
def ubah_produk(
    produk_id: int,
    data: ProdukUbah,
    sesi: Session = Depends(ambil_sesi),
    _: Pengguna = Depends(wajib_pemilik),
) -> ProdukKeluar:
    return ProdukKeluar.model_validate(layanan.ubah_produk(sesi, produk_id, data))


@rute.post("/produk/kilat", status_code=201)
def produk_kilat(
    data: ProdukKilat,
    sesi: Session = Depends(ambil_sesi),
    pengguna: Pengguna = Depends(pengguna_berjalan),
) -> Any:
    # Boleh dilakukan kasir: ia dipakai di tengah antrean, saat menemukan
    # barang yang belum terdaftar (STK-05).
    return _sesuai_peran(layanan.tambah_cepat(sesi, data, pengguna.id), pengguna)


@rute.post("/produk/{produk_id}/satuan", status_code=201)
def tambah_satuan(
    produk_id: int,
    data: SatuanMasuk,
    sesi: Session = Depends(ambil_sesi),
    _: Pengguna = Depends(wajib_pemilik),
) -> SatuanKeluar:
    return SatuanKeluar.model_validate(layanan.tambah_satuan(sesi, produk_id, data))


@rute.get("/produk/{produk_id}/kartu-stok", response_model=list[MutasiKeluar])
def kartu_stok(
    produk_id: int,
    sesi: Session = Depends(ambil_sesi),
    _: Pengguna = Depends(wajib_pemilik),
) -> Any:
    return layanan_stok.kartu_stok(sesi, produk_id)


@rute.get("/kategori", response_model=list[KategoriKeluar])
def daftar_kategori(
    sesi: Session = Depends(ambil_sesi),
    _: Pengguna = Depends(pengguna_berjalan),
) -> Any:
    return layanan.daftar_kategori(sesi)


@rute.post("/kategori", status_code=201, response_model=KategoriKeluar)
def buat_kategori(
    data: KategoriMasuk,
    sesi: Session = Depends(ambil_sesi),
    _: Pengguna = Depends(wajib_pemilik),
) -> Any:
    return layanan.buat_kategori(sesi, data.nama)


@rute.post("/penyesuaian-stok")
def penyesuaian_stok(
    data: PenyesuaianStok,
    sesi: Session = Depends(ambil_sesi),
    pemilik: Pengguna = Depends(wajib_pemilik),
) -> ProdukKeluar:
    produk = layanan.sesuaikan_stok(
        sesi, data.produk_id, data.jumlah, data.alasan, pemilik.id
    )
    return ProdukKeluar.model_validate(produk)


@rute.get("/stok/menipis")
def stok_menipis(
    sesi: Session = Depends(ambil_sesi),
    pemilik: Pengguna = Depends(wajib_pemilik),
) -> Any:
    return _sesuai_peran(layanan_stok.stok_menipis(sesi), pemilik)


@rute.get("/stok/minus")
def stok_minus(
    sesi: Session = Depends(ambil_sesi),
    pemilik: Pengguna = Depends(wajib_pemilik),
) -> Any:
    return _sesuai_peran(layanan_stok.stok_minus(sesi), pemilik)
