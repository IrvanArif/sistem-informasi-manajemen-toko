from enum import StrEnum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.model.dasar import Dasar, KolomWaktu


class Peran(StrEnum):
    pemilik = "pemilik"
    kasir = "kasir"


class Pengguna(Dasar, KolomWaktu):
    """Akun yang bisa masuk ke sistem.

    Tidak pernah dihapus. Akun yang tidak dipakai lagi dinonaktifkan lewat
    kolom `aktif`, karena nota dan mutasi stok merujuk penggunanya dan
    menghapus akun akan memutus jejak audit (bab 03 aturan integritas #6).
    """

    __tablename__ = "pengguna"

    id: Mapped[int] = mapped_column(primary_key=True)
    nama_pengguna: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nama_lengkap: Mapped[str] = mapped_column(String(100), nullable=False)
    sandi_hash: Mapped[str] = mapped_column(nullable=False)
    peran: Mapped[Peran] = mapped_column(Enum(Peran, name="peran"), nullable=False)
    aktif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Pengguna {self.nama_pengguna} ({self.peran.value})>"
