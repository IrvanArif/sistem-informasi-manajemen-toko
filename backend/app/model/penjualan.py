from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.dasar import Dasar, KolomWaktu
from app.model.produk import JUMLAH, TARIF


class MetodeBayar(StrEnum):
    tunai = "tunai"
    transfer = "transfer"
    qris = "qris"


class StatusNota(StrEnum):
    selesai = "selesai"
    sebagian_diretur = "sebagian_diretur"
    diretur_penuh = "diretur_penuh"


class Penjualan(Dasar, KolomWaktu):
    __tablename__ = "penjualan"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Kunci idempotensi, dibuat di perangkat. Kalau jaringan putus tepat
    # setelah server menyimpan tetapi sebelum jawabannya sampai, perangkat
    # akan mengirim ulang, dan server cukup menjawab "sudah ada".
    # Tanpa ini, satu gangguan jaringan menggandakan omzet.
    uuid_klien: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), unique=True, nullable=False
    )

    # Dibuat di perangkat juga. Nomor yang menunggu server berarti struk
    # yang dicetak saat internet mati tidak punya nomor.
    nomor_nota: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)

    sesi_kas_id: Mapped[int] = mapped_column(ForeignKey("sesi_kas.id"), index=True)
    kasir_id: Mapped[int] = mapped_column(ForeignKey("pengguna.id"), index=True)

    # Waktu kejadian di perangkat, dipakai seluruh laporan. Nota yang
    # dibuat saat internet mati baru sampai berjam-jam kemudian; memakai
    # waktu kedatangan akan memindahkan omzet Selasa ke hari Rabu.
    waktu_transaksi: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    waktu_diterima: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    subtotal: Mapped[int] = mapped_column(BigInteger, nullable=False)
    diskon_nota: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    pembulatan: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    total: Mapped[int] = mapped_column(BigInteger, nullable=False)

    metode_bayar: Mapped[MetodeBayar] = mapped_column(
        Enum(MetodeBayar, name="metode_bayar"), nullable=False
    )
    dibayar: Mapped[int] = mapped_column(BigInteger, nullable=False)
    kembalian: Mapped[int] = mapped_column(BigInteger, nullable=False)

    status: Mapped[StatusNota] = mapped_column(
        Enum(StatusNota, name="status_nota"), default=StatusNota.selesai, nullable=False
    )
    catatan: Mapped[str | None] = mapped_column(Text)

    item: Mapped[list["ItemPenjualan"]] = relationship(
        back_populates="penjualan", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Penjualan {self.nomor_nota} Rp{self.total}>"


class ItemPenjualan(Dasar, KolomWaktu):
    """Satu baris nota.

    Kolom bertanda salinan diisi saat transaksi dan tidak pernah dibaca
    ulang dari produk. Itulah yang membuat laporan laba bulan lalu tetap
    memberi angka yang sama meski harga hari ini sudah berubah.
    """

    __tablename__ = "item_penjualan"

    id: Mapped[int] = mapped_column(primary_key=True)
    penjualan_id: Mapped[int] = mapped_column(ForeignKey("penjualan.id"), index=True)
    produk_id: Mapped[int] = mapped_column(ForeignKey("produk.id"))
    satuan_id: Mapped[int] = mapped_column(ForeignKey("satuan_produk.id"))

    nama_produk: Mapped[str] = mapped_column(String(150), nullable=False)  # salinan
    nama_satuan: Mapped[str] = mapped_column(String(20), nullable=False)  # salinan
    faktor: Mapped[Decimal] = mapped_column(JUMLAH, nullable=False)  # salinan

    jumlah: Mapped[Decimal] = mapped_column(JUMLAH, nullable=False)
    jumlah_dasar: Mapped[Decimal] = mapped_column(JUMLAH, nullable=False)

    harga_satuan: Mapped[int] = mapped_column(BigInteger, nullable=False)  # salinan
    diskon: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    subtotal: Mapped[int] = mapped_column(BigInteger, nullable=False)
    hpp_saat_itu: Mapped[Decimal] = mapped_column(TARIF, nullable=False)  # salinan

    penjualan: Mapped[Penjualan] = relationship(back_populates="item")

    def __repr__(self) -> str:
        return f"<ItemPenjualan {self.nama_produk} x{self.jumlah}>"
