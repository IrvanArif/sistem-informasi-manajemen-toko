from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.model.produk import Produk, SatuanProduk


def produk_baru(sesi: Session, kode: str = "P001") -> Produk:
    p = Produk(kode=kode, nama="Indomie Goreng", satuan_dasar="bungkus")
    sesi.add(p)
    sesi.commit()
    return p


def test_jumlah_menyimpan_tiga_angka_desimal(sesi: Session) -> None:
    """Barang curah: 1,5 kg harus kembali persis 1,500, bukan 1,4999..."""
    p = produk_baru(sesi)
    p.stok = Decimal("1.500")
    sesi.commit()
    sesi.refresh(p)
    assert p.stok == Decimal("1.500")


def test_hpp_menyimpan_empat_angka_desimal(sesi: Session) -> None:
    """Angka ini diambil dari contoh terhitung di bab 03, bukan dari kode."""
    p = produk_baru(sesi)
    p.hpp = Decimal("2866.6667")
    sesi.commit()
    sesi.refresh(p)
    assert p.hpp == Decimal("2866.6667")


def test_stok_bawaan_nol(sesi: Session) -> None:
    assert produk_baru(sesi).stok == Decimal("0")


def test_faktor_nol_ditolak_basis_data(sesi: Session) -> None:
    """Ditolak di lapis basis data, bukan hanya di Python."""
    p = produk_baru(sesi)
    sesi.add(
        SatuanProduk(produk_id=p.id, nama="dus", faktor=Decimal("0"), harga_jual=1)
    )
    with pytest.raises(IntegrityError):
        sesi.commit()


def test_faktor_negatif_ditolak_basis_data(sesi: Session) -> None:
    p = produk_baru(sesi)
    sesi.add(
        SatuanProduk(produk_id=p.id, nama="dus", faktor=Decimal("-1"), harga_jual=1)
    )
    with pytest.raises(IntegrityError):
        sesi.commit()


def test_harga_negatif_ditolak_basis_data(sesi: Session) -> None:
    p = produk_baru(sesi)
    sesi.add(
        SatuanProduk(produk_id=p.id, nama="dus", faktor=Decimal("40"), harga_jual=-1)
    )
    with pytest.raises(IntegrityError):
        sesi.commit()


def test_barcode_wajib_unik_lintas_produk(sesi: Session) -> None:
    """Satu barcode tidak boleh menunjuk dua barang berbeda."""
    a = produk_baru(sesi, "P001")
    b = produk_baru(sesi, "P002")
    sesi.add(
        SatuanProduk(
            produk_id=a.id, nama="bungkus", faktor=Decimal("1"),
            harga_jual=3500, barcode="8991002101234", is_dasar=True,
        )
    )
    sesi.commit()
    sesi.add(
        SatuanProduk(
            produk_id=b.id, nama="bungkus", faktor=Decimal("1"),
            harga_jual=3000, barcode="8991002101234", is_dasar=True,
        )
    )
    with pytest.raises(IntegrityError):
        sesi.commit()


def test_barcode_boleh_kosong_di_banyak_satuan(sesi: Session) -> None:
    """Produk tanpa barcode itu wajar, dan tidak boleh saling bentrok."""
    p = produk_baru(sesi)
    for nama, faktor in (("bungkus", "1"), ("dus", "40")):
        sesi.add(
            SatuanProduk(
                produk_id=p.id, nama=nama, faktor=Decimal(faktor), harga_jual=1
            )
        )
    sesi.commit()
    assert len(p.satuan) == 2


def test_nama_satuan_unik_dalam_satu_produk(sesi: Session) -> None:
    p = produk_baru(sesi)
    for _ in range(2):
        sesi.add(
            SatuanProduk(
                produk_id=p.id, nama="dus", faktor=Decimal("40"), harga_jual=1
            )
        )
    with pytest.raises(IntegrityError):
        sesi.commit()


def test_kode_produk_unik(sesi: Session) -> None:
    produk_baru(sesi, "P001")
    sesi.add(Produk(kode="P001", nama="Lain", satuan_dasar="pcs"))
    with pytest.raises(IntegrityError):
        sesi.commit()


def test_harga_tiap_satuan_berdiri_sendiri(sesi: Session) -> None:
    """Satu dus Rp130.000, bukan 40 x Rp3.500. Selisih itu disengaja."""
    p = produk_baru(sesi)
    sesi.add_all(
        [
            SatuanProduk(produk_id=p.id, nama="bungkus", faktor=Decimal("1"),
                         harga_jual=3500, is_dasar=True),
            SatuanProduk(produk_id=p.id, nama="dus", faktor=Decimal("40"),
                         harga_jual=130_000),
        ]
    )
    sesi.commit()
    sesi.refresh(p)
    harga = {s.nama: s.harga_jual for s in p.satuan}
    assert harga["dus"] == 130_000
    assert harga["dus"] != harga["bungkus"] * 40
