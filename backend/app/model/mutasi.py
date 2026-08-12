from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.model.dasar import Dasar, KolomWaktu
from app.model.produk import JUMLAH, TARIF


class TipeMutasi(StrEnum):
    stok_awal = "stok_awal"
    penjualan = "penjualan"
    retur_penjualan = "retur_penjualan"
    pembelian = "pembelian"
    retur_pembelian = "retur_pembelian"
    penyesuaian = "penyesuaian"
    opname = "opname"


class MutasiStok(Dasar, KolomWaktu):
    """Buku besar stok. Sumber kebenaran, bukan salinan.

    Tabel ini HANYA menerima penambahan. Tidak ada UPDATE, tidak ada
    DELETE. Koreksi selalu berupa baris baru, karena itulah satu-satunya
    cara pertanyaan "kenapa stok gula kurang tiga?" tetap bisa dijawab
    berbulan-bulan kemudian (bab 03 aturan integritas #6).
    """

    __tablename__ = "mutasi_stok"

    id: Mapped[int] = mapped_column(primary_key=True)
    produk_id: Mapped[int] = mapped_column(ForeignKey("produk.id"), index=True)
    tipe: Mapped[TipeMutasi] = mapped_column(
        Enum(TipeMutasi, name="tipe_mutasi"), nullable=False
    )

    # Bertanda: negatif untuk keluar, positif untuk masuk. Selalu dalam
    # satuan dasar, sehingga saldonya bisa dijumlahkan tanpa konversi.
    jumlah: Mapped[Decimal] = mapped_column(JUMLAH, nullable=False)

    saldo_sesudah: Mapped[Decimal] = mapped_column(JUMLAH, nullable=False)
    hpp_saat_itu: Mapped[Decimal] = mapped_column(TARIF, nullable=False)

    rujukan_tipe: Mapped[str | None] = mapped_column(String(30))
    rujukan_id: Mapped[int | None] = mapped_column()

    # Wajib terisi untuk tipe penyesuaian. Kolom alasan yang boleh kosong
    # akan selalu kosong, dan enam bulan lagi tidak ada yang ingat kenapa
    # stok berubah.
    alasan: Mapped[str | None] = mapped_column(Text)

    pengguna_id: Mapped[int] = mapped_column(ForeignKey("pengguna.id"))

    def __repr__(self) -> str:
        return f"<MutasiStok {self.tipe} {self.jumlah:+} -> {self.saldo_sesudah}>"
