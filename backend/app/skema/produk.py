from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

# Jumlah dikirim sebagai string, bukan angka JSON. Angka dalam JSON adalah
# pecahan biner 64-bit, sehingga NUMERIC(14,3) yang lewat sana kembali
# dengan nilai yang tidak persis sama (bab 07 §7.1).
#
# Angka desimalnya dipatok, bukan sekadar diubah menjadi teks apa adanya.
# Tanpa itu, bentuk jawaban bergantung pada dari mana objeknya datang:
# produk yang baru dibuat mengirim "40", sementara produk yang sama
# setelah dibaca ulang dari basis data mengirim "40.000". Pemakai di sisi
# browser lalu harus menebak, dan perbandingan teks menjadi tidak bisa
# dipercaya.
TIGA = Decimal("0.001")
EMPAT = Decimal("0.0001")


def _tiga_desimal(n: Decimal) -> str:
    return str(n.quantize(TIGA))


def _empat_desimal(n: Decimal) -> str:
    return str(n.quantize(EMPAT))


Jumlah = Annotated[Decimal, PlainSerializer(_tiga_desimal, return_type=str)]
Tarif = Annotated[Decimal, PlainSerializer(_empat_desimal, return_type=str)]


class SatuanKeluar(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nama: str
    faktor: Jumlah
    harga_jual: int
    barcode: str | None
    is_dasar: bool
    aktif: bool


class SatuanMasuk(BaseModel):
    nama: str = Field(min_length=1, max_length=20)
    faktor: Decimal = Field(gt=0)
    harga_jual: int = Field(ge=0)
    barcode: str | None = Field(default=None, max_length=32)
    is_dasar: bool = False


class ProdukKeluar(BaseModel):
    """Bentuk lengkap, untuk peran pemilik."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    kode: str
    nama: str
    kategori_id: int | None
    satuan_dasar: str
    stok: Jumlah
    stok_minimum: Jumlah
    hpp: Tarif
    perlu_dilengkapi: bool
    aktif: bool
    satuan: list[SatuanKeluar]


class ProdukKeluarKasir(BaseModel):
    """Bentuk untuk peran kasir: TANPA hpp.

    Kolomnya disebut satu per satu, bukan mewarisi lalu membuang, supaya
    kolom sensitif yang ditambahkan kelak tidak ikut bocor karena lupa
    dibuang (bab 08 §8.1).
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    kode: str
    nama: str
    kategori_id: int | None
    satuan_dasar: str
    stok: Jumlah
    stok_minimum: Jumlah
    perlu_dilengkapi: bool
    aktif: bool
    satuan: list[SatuanKeluar]


class ProdukMasuk(BaseModel):
    kode: str = Field(min_length=1, max_length=30)
    nama: str = Field(min_length=1, max_length=150)
    kategori_id: int | None = None
    satuan_dasar: str = Field(min_length=1, max_length=20)
    stok_minimum: Decimal = Field(default=Decimal("0"), ge=0)
    stok_awal: Decimal = Field(default=Decimal("0"))
    satuan: list[SatuanMasuk] = Field(min_length=1)


class ProdukUbah(BaseModel):
    nama: str | None = Field(default=None, min_length=1, max_length=150)
    kategori_id: int | None = None
    stok_minimum: Decimal | None = Field(default=None, ge=0)
    perlu_dilengkapi: bool | None = None
    aktif: bool | None = None


class ProdukKilat(BaseModel):
    """Tambah cepat saat transaksi: nama dan harga saja (STK-05)."""

    nama: str = Field(min_length=1, max_length=150)
    harga: int = Field(ge=0)
    uuid_klien: UUID | None = None


class KategoriKeluar(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nama: str


class KategoriMasuk(BaseModel):
    nama: str = Field(min_length=1, max_length=60)


class PenyesuaianStok(BaseModel):
    produk_id: int
    jumlah: Decimal
    alasan: str = Field(min_length=3)


class MutasiKeluar(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipe: str
    jumlah: Jumlah
    saldo_sesudah: Jumlah
    hpp_saat_itu: Tarif
    rujukan_tipe: str | None
    rujukan_id: int | None
    alasan: str | None
    pengguna_id: int
