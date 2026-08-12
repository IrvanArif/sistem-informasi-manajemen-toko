from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.model.dasar import Dasar, KolomWaktu


class Kategori(Dasar, KolomWaktu):
    __tablename__ = "kategori"

    id: Mapped[int] = mapped_column(primary_key=True)
    nama: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Kategori {self.nama}>"
