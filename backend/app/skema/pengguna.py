from pydantic import BaseModel, ConfigDict, Field

from app.model.pengguna import Peran


class PenggunaKeluar(BaseModel):
    """Bentuk pengguna yang dikirim keluar.

    sandi_hash sengaja tidak ada di sini. Bentuk keluaran yang menyebut
    kolomnya satu per satu lebih aman daripada yang membuang beberapa,
    karena kolom sensitif yang ditambahkan kelak tidak ikut bocor.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    nama_pengguna: str
    nama_lengkap: str
    peran: Peran
    aktif: bool


class BuatPengguna(BaseModel):
    nama_pengguna: str = Field(min_length=3, max_length=50)
    nama_lengkap: str = Field(min_length=1, max_length=100)
    sandi: str = Field(min_length=8)
    peran: Peran


class UbahPengguna(BaseModel):
    nama_lengkap: str | None = Field(default=None, min_length=1, max_length=100)
    peran: Peran | None = None
    aktif: bool | None = None


class AturUlangSandi(BaseModel):
    sandi_baru: str = Field(min_length=8)
