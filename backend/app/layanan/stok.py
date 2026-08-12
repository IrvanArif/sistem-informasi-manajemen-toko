from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.kesalahan import KesalahanDomain
from app.model.mutasi import MutasiStok, TipeMutasi
from app.model.produk import Produk

NOL = Decimal("0")


def catat_mutasi(
    sesi: Session,
    produk_id: int,
    tipe: TipeMutasi,
    jumlah_dasar: Decimal,
    pengguna_id: int,
    alasan: str | None = None,
    rujukan_tipe: str | None = None,
    rujukan_id: int | None = None,
) -> MutasiStok:
    """Menulis satu baris buku besar dan memperbarui salinan stok.

    Keduanya terjadi dalam transaksi yang sama. Kalau salah satu gagal,
    keduanya batal, sehingga buku besar dan salinan tidak pernah
    berselisih (bab 03 aturan integritas #1).
    """
    # Baris produk dikunci lebih dulu. Tanpa ini, dua mutasi yang tiba
    # nyaris bersamaan membaca stok yang sama, lalu keduanya menulis
    # saldo_sesudah dari angka yang sudah basi. Hal itu bukan teori: ia
    # terjadi setiap kali antrean offline dikirim beruntun.
    produk = sesi.execute(
        select(Produk).where(Produk.id == produk_id).with_for_update()
    ).scalar_one_or_none()

    if produk is None:
        raise KesalahanDomain(
            "PRODUK_TIDAK_DITEMUKAN", "Produk tidak ditemukan", status=404
        )

    if tipe is TipeMutasi.penyesuaian and not (alasan or "").strip():
        raise KesalahanDomain(
            "ALASAN_WAJIB",
            "Penyesuaian stok harus disertai alasan. Tanpa itu, enam bulan "
            "lagi tidak ada yang tahu kenapa stoknya berubah.",
        )

    saldo_baru = produk.stok + jumlah_dasar

    # Stok yang menjadi negatif TIDAK dihalangi. Menolak penjualan barang
    # yang jelas ada di tangan pembeli akan membuat kasir meninggalkan
    # sistem, dan angka minus justru penanda jujur bahwa ada barang masuk
    # yang belum tercatat (ADR-0006).
    mutasi = MutasiStok(
        produk_id=produk.id,
        tipe=tipe,
        jumlah=jumlah_dasar,
        saldo_sesudah=saldo_baru,
        hpp_saat_itu=produk.hpp,
        alasan=alasan,
        rujukan_tipe=rujukan_tipe,
        rujukan_id=rujukan_id,
        pengguna_id=pengguna_id,
    )
    sesi.add(mutasi)
    produk.stok = saldo_baru
    sesi.flush()
    return mutasi


def kartu_stok(sesi: Session, produk_id: int) -> list[MutasiStok]:
    """Seluruh mutasi satu produk, terlama lebih dulu."""
    return list(
        sesi.execute(
            select(MutasiStok)
            .where(MutasiStok.produk_id == produk_id)
            .order_by(MutasiStok.id)
        ).scalars()
    )


def stok_menipis(sesi: Session) -> list[Produk]:
    return list(
        sesi.execute(
            select(Produk)
            .where(Produk.aktif.is_(True), Produk.stok <= Produk.stok_minimum)
            .order_by(Produk.nama)
        ).scalars()
    )


def stok_minus(sesi: Session) -> list[Produk]:
    return list(
        sesi.execute(
            select(Produk).where(Produk.stok < NOL).order_by(Produk.nama)
        ).scalars()
    )


def periksa_keselarasan(sesi: Session) -> list[tuple[int, Decimal, Decimal]]:
    """Mencari produk yang salinan stoknya berbeda dari buku besarnya.

    Hasil yang tidak kosong berarti ada bug, bukan data yang perlu
    dirapikan diam-diam (bab 03 §3.3).

    Mengembalikan daftar (produk_id, stok_tersimpan, saldo_buku_besar).
    """
    saldo = (
        select(
            MutasiStok.produk_id.label("produk_id"),
            func.coalesce(func.sum(MutasiStok.jumlah), NOL).label("saldo"),
        )
        .group_by(MutasiStok.produk_id)
        .subquery()
    )
    kueri = (
        select(Produk.id, Produk.stok, func.coalesce(saldo.c.saldo, NOL))
        .outerjoin(saldo, saldo.c.produk_id == Produk.id)
        .where(Produk.stok != func.coalesce(saldo.c.saldo, NOL))
    )
    return [(i, s, b) for i, s, b in sesi.execute(kueri).all()]
