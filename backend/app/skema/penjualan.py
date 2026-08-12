from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.model.penjualan import MetodeBayar
from app.skema.produk import Jumlah, ProdukKilat, Tarif


class ItemMasuk(BaseModel):
    """Satu baris nota yang dikirim perangkat.

    Merujuk produk lewat `produk_id` + `satuan_id` (produk yang sudah
    dikenal) ATAU lewat `produk_baru` (hasil tambah cepat, termasuk yang
    dibuat saat offline). Tidak pernah keduanya (bab 05 §5.5).
    """

    produk_id: int | None = None
    satuan_id: int | None = None
    produk_baru: ProdukKilat | None = None
    jumlah: Decimal = Field(gt=0)
    harga_satuan: int = Field(ge=0)
    diskon: int = Field(default=0, ge=0)
    subtotal: int = Field(ge=0)

    @model_validator(mode="after")
    def tepat_satu_rujukan(self) -> "ItemMasuk":
        punya_lama = self.produk_id is not None
        punya_baru = self.produk_baru is not None
        if punya_lama == punya_baru:
            raise ValueError(
                "Baris nota harus merujuk produk_id atau produk_baru, tidak keduanya"
            )
        if punya_lama and self.satuan_id is None:
            raise ValueError("produk_id harus disertai satuan_id")
        return self


class PenjualanMasuk(BaseModel):
    uuid_klien: UUID
    nomor_nota: str = Field(min_length=1, max_length=30)
    waktu_transaksi: datetime
    metode_bayar: MetodeBayar = MetodeBayar.tunai
    diskon_nota: int = Field(default=0, ge=0)
    pembulatan: int = 0
    total: int = Field(ge=0)
    dibayar: int = Field(ge=0)
    kembalian: int = Field(ge=0)
    catatan: str | None = None
    item: list[ItemMasuk] = Field(min_length=1)


class ItemKeluar(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    produk_id: int
    nama_produk: str
    nama_satuan: str
    jumlah: Jumlah
    jumlah_dasar: Jumlah
    harga_satuan: int
    diskon: int
    subtotal: int
    hpp_saat_itu: Tarif


class PenjualanKeluar(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid_klien: UUID
    nomor_nota: str
    sesi_kas_id: int
    kasir_id: int
    waktu_transaksi: datetime
    subtotal: int
    diskon_nota: int
    pembulatan: int
    total: int
    metode_bayar: MetodeBayar
    dibayar: int
    kembalian: int
    status: str
    item: list[ItemKeluar]


class BukaSesi(BaseModel):
    modal_awal: int = Field(ge=0)


class TutupSesi(BaseModel):
    kas_fisik: int = Field(ge=0)
    catatan: str | None = None


class SesiKasKeluar(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kasir_id: int
    waktu_buka: datetime
    modal_awal: int
    waktu_tutup: datetime | None
    kas_sistem: int | None
    kas_fisik: int | None
    selisih: int | None
    catatan: str | None
    status: str
