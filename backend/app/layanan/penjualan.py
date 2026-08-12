from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.kesalahan import KesalahanDomain
from app.layanan.kas import wajib_sesi_terbuka
from app.layanan.produk import tambah_cepat
from app.layanan.satuan import cari_satuan, ke_satuan_dasar, satuan_dasar_dari
from app.layanan.stok import catat_mutasi
from app.model.mutasi import MutasiStok, TipeMutasi
from app.model.penjualan import ItemPenjualan, Penjualan
from app.model.produk import Produk, SatuanProduk
from app.skema.penjualan import ItemMasuk, PenjualanMasuk

NOL = Decimal("0")


def _hpp_pada(sesi: Session, produk: Produk, waktu: datetime) -> Decimal:
    """HPP produk pada saat transaksi terjadi, bukan HPP sekarang.

    Nota yang dibuat saat internet mati baru sampai berjam-jam kemudian.
    Bila di sela itu ada penerimaan barang yang mengubah HPP, memakai HPP
    sekarang akan menghitung laba transaksi pagi dengan harga modal sore
    (bab 05 §5.5).
    """
    terakhir = sesi.execute(
        select(MutasiStok.hpp_saat_itu)
        .where(MutasiStok.produk_id == produk.id, MutasiStok.dibuat_pada <= waktu)
        .order_by(MutasiStok.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    return terakhir if terakhir is not None else produk.hpp


def _resolusi_produk(
    sesi: Session, baris: ItemMasuk, kasir_id: int
) -> tuple[Produk, SatuanProduk]:
    if baris.produk_baru is not None:
        produk = tambah_cepat(sesi, baris.produk_baru, kasir_id)
        return produk, satuan_dasar_dari(produk)

    tersimpan = sesi.get(Produk, baris.produk_id or 0)
    if tersimpan is None:
        raise KesalahanDomain(
            "PRODUK_TIDAK_DITEMUKAN",
            f"Produk {baris.produk_id} tidak ditemukan",
            status=404,
        )
    return tersimpan, cari_satuan(tersimpan, baris.satuan_id or 0)


def catat_penjualan(
    sesi: Session, data: PenjualanMasuk, kasir_id: int
) -> tuple[Penjualan, bool]:
    """Menyimpan satu nota. Mengembalikan (nota, baru_dibuat).

    Idempoten terhadap uuid_klien: bila nota dengan UUID itu sudah ada,
    yang tersimpan dikembalikan apa adanya tanpa memotong stok lagi.
    Inilah yang membuat pengiriman ulang selalu aman. Tanpa ini, satu
    gangguan jaringan bisa menggandakan omzet (bab 03 aturan #6).
    """
    sudah_ada = sesi.execute(
        select(Penjualan).where(Penjualan.uuid_klien == data.uuid_klien)
    ).scalar_one_or_none()
    if sudah_ada is not None:
        return sudah_ada, False

    kas = wajib_sesi_terbuka(sesi, kasir_id)

    bentrok = sesi.execute(
        select(Penjualan).where(Penjualan.nomor_nota == data.nomor_nota)
    ).scalar_one_or_none()
    if bentrok is not None:
        raise KesalahanDomain(
            "NOTA_GANDA",
            f"Nomor nota {data.nomor_nota} sudah dipakai transaksi lain",
            detail={"nomor_nota": data.nomor_nota},
        )

    nota = Penjualan(
        uuid_klien=data.uuid_klien,
        nomor_nota=data.nomor_nota,
        sesi_kas_id=kas.id,
        kasir_id=kasir_id,
        waktu_transaksi=data.waktu_transaksi,
        waktu_diterima=datetime.now(UTC),
        subtotal=0,
        diskon_nota=data.diskon_nota,
        pembulatan=data.pembulatan,
        total=0,
        metode_bayar=data.metode_bayar,
        dibayar=data.dibayar,
        kembalian=data.kembalian,
        catatan=data.catatan,
    )
    sesi.add(nota)
    sesi.flush()

    subtotal_nota = 0
    for baris in data.item:
        produk, satuan = _resolusi_produk(sesi, baris, kasir_id)

        # Server menghitung ulang subtotal baris. Yang diterima apa adanya
        # hanya harga_satuan, karena angka itulah yang tercetak di struk
        # dan disepakati pembeli. Penjumlahannya tidak boleh dipercayakan
        # ke perangkat (bab 07 §7.6).
        hitung = int(baris.harga_satuan * baris.jumlah) - baris.diskon
        if hitung != baris.subtotal:
            raise KesalahanDomain(
                "TOTAL_TIDAK_COCOK",
                f"Subtotal baris {produk.nama} tidak cocok: "
                f"dikirim {baris.subtotal}, dihitung ulang {hitung}",
                detail={"dikirim": baris.subtotal, "dihitung": hitung},
            )

        jumlah_dasar = ke_satuan_dasar(baris.jumlah, satuan.faktor)
        hpp = _hpp_pada(sesi, produk, data.waktu_transaksi)

        sesi.add(
            ItemPenjualan(
                penjualan_id=nota.id,
                produk_id=produk.id,
                satuan_id=satuan.id,
                nama_produk=produk.nama,
                nama_satuan=satuan.nama,
                faktor=satuan.faktor,
                jumlah=baris.jumlah,
                jumlah_dasar=jumlah_dasar,
                harga_satuan=baris.harga_satuan,
                diskon=baris.diskon,
                subtotal=hitung,
                hpp_saat_itu=hpp,
            )
        )
        catat_mutasi(
            sesi,
            produk.id,
            TipeMutasi.penjualan,
            -jumlah_dasar,
            kasir_id,
            rujukan_tipe="penjualan",
            rujukan_id=nota.id,
        )
        subtotal_nota += hitung

    total = subtotal_nota - data.diskon_nota + data.pembulatan
    if total != data.total:
        raise KesalahanDomain(
            "TOTAL_TIDAK_COCOK",
            f"Total nota tidak cocok: dikirim {data.total}, dihitung ulang {total}",
            detail={"dikirim": data.total, "dihitung": total},
        )

    nota.subtotal = subtotal_nota
    nota.total = total
    sesi.commit()
    return nota, True


def daftar_penjualan(
    sesi: Session,
    dari: datetime | None = None,
    sampai: datetime | None = None,
    batas: int = 100,
) -> list[Penjualan]:
    kueri = select(Penjualan).order_by(Penjualan.waktu_transaksi.desc()).limit(batas)
    if dari is not None:
        kueri = kueri.where(Penjualan.waktu_transaksi >= dari)
    if sampai is not None:
        kueri = kueri.where(Penjualan.waktu_transaksi <= sampai)
    return list(sesi.execute(kueri).scalars())
