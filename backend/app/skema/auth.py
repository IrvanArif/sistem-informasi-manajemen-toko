from pydantic import BaseModel, Field


class PermintaanMasuk(BaseModel):
    nama_pengguna: str
    sandi: str


class JawabanToken(BaseModel):
    token_akses: str
    token_segar: str


class PermintaanSegarkan(BaseModel):
    token_segar: str


class UbahSandiSendiri(BaseModel):
    sandi_lama: str
    sandi_baru: str = Field(min_length=8)
