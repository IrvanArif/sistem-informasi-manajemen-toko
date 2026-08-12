from datetime import datetime
from enum import StrEnum

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.model.dasar import Dasar, KolomWaktu


class StatusSesi(StrEnum):
    terbuka = "terbuka"
    tertutup = "tertutup"


class SesiKas(Dasar, KolomWaktu):
    """Satu periode kerja kasir, dari isi modal awal sampai hitung penutup.

    Tanpa sesi, kas fisik tidak bisa dicocokkan di akhir hari, dan selisih
    yang muncul tidak bisa dilekatkan pada siapa pun.
    """

    __tablename__ = "sesi_kas"

    id: Mapped[int] = mapped_column(primary_key=True)
    kasir_id: Mapped[int] = mapped_column(ForeignKey("pengguna.id"), index=True)
    waktu_buka: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    modal_awal: Mapped[int] = mapped_column(BigInteger, nullable=False)

    waktu_tutup: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    kas_sistem: Mapped[int | None] = mapped_column(BigInteger)
    kas_fisik: Mapped[int | None] = mapped_column(BigInteger)

    # Boleh negatif maupun positif. Sistem tidak pernah membetulkannya:
    # selisih adalah kenyataan yang perlu dilihat, bukan angka yang perlu
    # dirapikan (bab 04 §4.1).
    selisih: Mapped[int | None] = mapped_column(BigInteger)

    catatan: Mapped[str | None] = mapped_column(Text)
    status: Mapped[StatusSesi] = mapped_column(
        Enum(StatusSesi, name="status_sesi"), default=StatusSesi.terbuka, nullable=False
    )

    def __repr__(self) -> str:
        return f"<SesiKas #{self.id} {self.status}>"
