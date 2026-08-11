from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Dasar(DeclarativeBase):
    pass


class KolomWaktu:
    """Kolom waktu yang dipakai hampir semua tabel.

    `diubah_pada` diberi indeks sejak sekarang karena sinkronisasi
    beda-saja di M3 bergantung padanya (bab 05 §5.4).
    """

    dibuat_pada: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    diubah_pada: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
    )
