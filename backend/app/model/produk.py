from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.dasar import Dasar, KolomWaktu

# Ketelitian sampai satu gram. Tidak pernah float: dalam float,
# 0.1 + 0.2 tidak menghasilkan 0.3, dan selisih sekecil itu menumpuk
# lintas ribuan transaksi menjadi selisih stok yang tak bisa dijelaskan.
JUMLAH = Numeric(14, 3)

# HPP berdesimal, satu-satunya pengecualian dari aturan uang bilangan
# bulat rupiah. Ia tarif turunan yang dikalikan faktor satuan, bukan
# jumlah yang dibayarkan siapa pun (bab 03 §3.4).
TARIF = Numeric(14, 4)


class Produk(Dasar, KolomWaktu):
    __tablename__ = "produk"

    id: Mapped[int] = mapped_column(primary_key=True)
    kode: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    nama: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    kategori_id: Mapped[int | None] = mapped_column(ForeignKey("kategori.id"))
    satuan_dasar: Mapped[str] = mapped_column(String(20), nullable=False)

    # Salinan cepat, BUKAN sumber kebenaran. Yang sah adalah jumlah
    # seluruh baris mutasi_stok. Keduanya ditulis dalam satu transaksi,
    # dan bila berselisih, buku besar yang menang (bab 03 aturan #1).
    stok: Mapped[Decimal] = mapped_column(JUMLAH, default=Decimal("0"), nullable=False)

    stok_minimum: Mapped[Decimal] = mapped_column(
        JUMLAH, default=Decimal("0"), nullable=False
    )
    hpp: Mapped[Decimal] = mapped_column(TARIF, default=Decimal("0"), nullable=False)
    perlu_dilengkapi: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Kunci idempotensi untuk produk yang lahir dari "tambah cepat" saat
    # offline. Kosong untuk produk yang dibuat lewat katalog (bab 05).
    uuid_klien: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), unique=True)

    aktif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    satuan: Mapped[list["SatuanProduk"]] = relationship(
        back_populates="produk", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Produk {self.kode} {self.nama}>"


class SatuanProduk(Dasar, KolomWaktu):
    """Satu cara menjual sebuah produk.

    Harga tiap satuan ditulis sendiri, bukan dihitung dari perkalian
    faktor. Satu dus Rp130.000, bukan 40 x Rp3.500, dan justru selisih
    itulah alasan pembeli mengambil per dus (ADR-0005).
    """

    __tablename__ = "satuan_produk"
    __table_args__ = (
        UniqueConstraint("produk_id", "nama", name="uq_satuan_produk_nama"),
        CheckConstraint("faktor > 0", name="ck_satuan_faktor_positif"),
        CheckConstraint("harga_jual >= 0", name="ck_satuan_harga_tak_negatif"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    produk_id: Mapped[int] = mapped_column(ForeignKey("produk.id"), index=True)
    nama: Mapped[str] = mapped_column(String(20), nullable=False)
    faktor: Mapped[Decimal] = mapped_column(JUMLAH, nullable=False)
    harga_jual: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    # Barcode menempel pada satuan, bukan pada produk: dus punya barcode
    # sendiri, sehingga satu pindaian menentukan produk dan satuannya
    # sekaligus, dan kasir tidak perlu memilih apa pun.
    barcode: Mapped[str | None] = mapped_column(String(32), unique=True)

    is_dasar: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    aktif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    produk: Mapped[Produk] = relationship(back_populates="satuan")

    def __repr__(self) -> str:
        return f"<SatuanProduk {self.nama} x{self.faktor}>"
