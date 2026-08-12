from pydantic import BaseModel


class BarisGagal(BaseModel):
    baris: int
    alasan: str


class HasilImpor(BaseModel):
    """Hasil pratinjau maupun penjalanan impor.

    Kegagalan dilaporkan per baris dengan nomor barisnya, bukan sebagai
    satu pesan "impor gagal". Pemilik yang mengimpor ratusan produk perlu
    tahu baris mana yang harus dibetulkan, bukan sekadar bahwa ada yang
    salah (STK-04).
    """

    sah: int
    gagal: list[BarisGagal]
    tersimpan: int = 0
