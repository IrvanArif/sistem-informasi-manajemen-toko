from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.model.dasar import Dasar, KolomWaktu


class TokenSegar(Dasar, KolomWaktu):
    """Token segar yang masih berlaku.

    Yang disimpan adalah hash SHA-256 tokennya, bukan tokennya sendiri.
    Basis data yang bocor karena itu tidak menyerahkan sesi siapa pun,
    sama seperti tabel sandi yang menyimpan hash alih-alih sandi.
    """

    __tablename__ = "token_segar"

    id: Mapped[int] = mapped_column(primary_key=True)
    pengguna_id: Mapped[int] = mapped_column(ForeignKey("pengguna.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    kedaluwarsa_pada: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    dicabut_pada: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
