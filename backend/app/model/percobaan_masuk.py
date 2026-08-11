from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.model.dasar import Dasar, KolomWaktu


class PercobaanMasuk(Dasar, KolomWaktu):
    """Catatan setiap percobaan masuk, berhasil maupun gagal.

    Dipakai untuk membatasi percobaan berulang, dan menjadi jejak audit
    saat ada yang mencoba menebak sandi.
    """

    __tablename__ = "percobaan_masuk"

    id: Mapped[int] = mapped_column(primary_key=True)
    nama_pengguna: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    alamat_ip: Mapped[str] = mapped_column(String(45), index=True, nullable=False)
    berhasil: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
