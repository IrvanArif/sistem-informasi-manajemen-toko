import threading
from decimal import Decimal

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.keamanan.sandi import hash_sandi
from app.kesalahan import KesalahanDomain
from app.layanan.stok import (
    catat_mutasi,
    kartu_stok,
    periksa_keselarasan,
    stok_menipis,
    stok_minus,
)
from app.model.mutasi import TipeMutasi
from app.model.pengguna import Pengguna, Peran
from app.model.produk import Produk


@pytest.fixture
def pemilik(sesi: Session) -> Pengguna:
    p = Pengguna(
        nama_pengguna="irvan",
        nama_lengkap="Irvan",
        sandi_hash=hash_sandi("rahasia123"),
        peran=Peran.pemilik,
    )
    sesi.add(p)
    sesi.commit()
    return p


@pytest.fixture
def produk(sesi: Session) -> Produk:
    p = Produk(kode="P001", nama="Indomie Goreng", satuan_dasar="bungkus")
    sesi.add(p)
    sesi.commit()
    return p


def test_mutasi_menambah_stok(sesi: Session, produk: Produk, pemilik: Pengguna) -> None:
    catat_mutasi(sesi, produk.id, TipeMutasi.stok_awal, Decimal("80"), pemilik.id)
    sesi.commit()
    sesi.refresh(produk)
    assert produk.stok == Decimal("80")


def test_saldo_sesudah_berurutan(sesi: Session, produk: Produk, pemilik: Pengguna) -> None:
    """Tiga mutasi berturut-turut menghasilkan saldo yang menyambung."""
    for tipe, jumlah in (
        (TipeMutasi.stok_awal, "80"),
        (TipeMutasi.pembelian, "40"),
        (TipeMutasi.penjualan, "-3"),
    ):
        catat_mutasi(sesi, produk.id, tipe, Decimal(jumlah), pemilik.id)
    sesi.commit()

    saldo = [m.saldo_sesudah for m in kartu_stok(sesi, produk.id)]
    assert saldo == [Decimal("80"), Decimal("120"), Decimal("117")]


def test_salinan_stok_sama_dengan_jumlah_buku_besar(
    sesi: Session, produk: Produk, pemilik: Pengguna
) -> None:
    """Aturan integritas #1, diperiksa langsung."""
    for jumlah in ("80", "-3", "40", "-1.5"):
        catat_mutasi(sesi, produk.id, TipeMutasi.penyesuaian, Decimal(jumlah),
                     pemilik.id, alasan="uji")
    sesi.commit()
    sesi.refresh(produk)

    total = sum((m.jumlah for m in kartu_stok(sesi, produk.id)), Decimal("0"))
    assert produk.stok == total
    assert periksa_keselarasan(sesi) == []


def test_jumlah_pecahan_utuh(sesi: Session, produk: Produk, pemilik: Pengguna) -> None:
    catat_mutasi(sesi, produk.id, TipeMutasi.stok_awal, Decimal("42.500"), pemilik.id)
    catat_mutasi(sesi, produk.id, TipeMutasi.penjualan, Decimal("-1.500"), pemilik.id)
    sesi.commit()
    sesi.refresh(produk)
    assert produk.stok == Decimal("41.000")


def test_penyesuaian_tanpa_alasan_ditolak(
    sesi: Session, produk: Produk, pemilik: Pengguna
) -> None:
    with pytest.raises(KesalahanDomain) as e:
        catat_mutasi(sesi, produk.id, TipeMutasi.penyesuaian, Decimal("-1"), pemilik.id)
    assert e.value.kode == "ALASAN_WAJIB"


def test_penyesuaian_dengan_alasan_kosong_juga_ditolak(
    sesi: Session, produk: Produk, pemilik: Pengguna
) -> None:
    with pytest.raises(KesalahanDomain) as e:
        catat_mutasi(sesi, produk.id, TipeMutasi.penyesuaian, Decimal("-1"),
                     pemilik.id, alasan="   ")
    assert e.value.kode == "ALASAN_WAJIB"


def test_tipe_lain_tidak_menuntut_alasan(
    sesi: Session, produk: Produk, pemilik: Pengguna
) -> None:
    catat_mutasi(sesi, produk.id, TipeMutasi.penjualan, Decimal("-1"), pemilik.id)
    sesi.commit()


def test_stok_boleh_menjadi_minus(
    sesi: Session, produk: Produk, pemilik: Pengguna
) -> None:
    """ADR-0006: menolak penjualan barang yang jelas ada akan membuat
    kasir meninggalkan sistem. Minus dicatat, bukan dihalangi."""
    catat_mutasi(sesi, produk.id, TipeMutasi.penjualan, Decimal("-3"), pemilik.id)
    sesi.commit()
    sesi.refresh(produk)
    assert produk.stok == Decimal("-3")
    assert [p.id for p in stok_minus(sesi)] == [produk.id]


def test_mutasi_menyimpan_hpp_saat_itu(
    sesi: Session, produk: Produk, pemilik: Pengguna
) -> None:
    """Laba historis dihitung dari HPP yang tersimpan, bukan HPP hari ini."""
    produk.hpp = Decimal("2866.6667")
    sesi.commit()
    m = catat_mutasi(sesi, produk.id, TipeMutasi.penjualan, Decimal("-1"), pemilik.id)
    sesi.commit()
    assert m.hpp_saat_itu == Decimal("2866.6667")


def test_kartu_stok_menyimpan_rujukan(
    sesi: Session, produk: Produk, pemilik: Pengguna
) -> None:
    catat_mutasi(sesi, produk.id, TipeMutasi.penjualan, Decimal("-2"), pemilik.id,
                 rujukan_tipe="penjualan", rujukan_id=77)
    sesi.commit()
    m = kartu_stok(sesi, produk.id)[0]
    assert (m.rujukan_tipe, m.rujukan_id) == ("penjualan", 77)


def test_produk_tak_dikenal_ditolak(sesi: Session, pemilik: Pengguna) -> None:
    with pytest.raises(KesalahanDomain) as e:
        catat_mutasi(sesi, 999_999, TipeMutasi.stok_awal, Decimal("1"), pemilik.id)
    assert e.value.kode == "PRODUK_TIDAK_DITEMUKAN"


def test_stok_menipis_terdeteksi(
    sesi: Session, produk: Produk, pemilik: Pengguna
) -> None:
    produk.stok_minimum = Decimal("10")
    sesi.commit()
    catat_mutasi(sesi, produk.id, TipeMutasi.stok_awal, Decimal("8"), pemilik.id)
    sesi.commit()
    assert [p.id for p in stok_menipis(sesi)] == [produk.id]


def test_stok_cukup_tidak_muncul_di_daftar_menipis(
    sesi: Session, produk: Produk, pemilik: Pengguna
) -> None:
    produk.stok_minimum = Decimal("10")
    sesi.commit()
    catat_mutasi(sesi, produk.id, TipeMutasi.stok_awal, Decimal("50"), pemilik.id)
    sesi.commit()
    assert stok_menipis(sesi) == []


def test_pemeriksa_keselarasan_menangkap_selisih(
    sesi: Session, produk: Produk, pemilik: Pengguna
) -> None:
    """Kalau salinan stok dirusak langsung, pemeriksa harus menemukannya."""
    catat_mutasi(sesi, produk.id, TipeMutasi.stok_awal, Decimal("80"), pemilik.id)
    sesi.commit()
    assert periksa_keselarasan(sesi) == []

    produk.stok = Decimal("999")  # meniru bug yang menulis salinan tanpa mutasi
    sesi.commit()

    selisih = periksa_keselarasan(sesi)
    assert len(selisih) == 1
    assert selisih[0][0] == produk.id
    assert selisih[0][1] == Decimal("999")
    assert selisih[0][2] == Decimal("80")


def test_dua_mutasi_bersamaan_tidak_saling_menimpa(
    mesin_uji: Engine, sesi: Session, produk: Produk, pemilik: Pengguna
) -> None:
    """Penguncian baris, diuji dengan dua sambungan sungguhan.

    Tanpa SELECT FOR UPDATE, kedua utas membaca stok yang sama lalu
    menulis saldo_sesudah dari angka yang sudah basi, dan salah satu
    mutasi hilang jejaknya. Ini bukan kejadian langka: ia terjadi setiap
    kali antrean offline dikirim beruntun (bab 03 aturan integritas #2).
    """
    produk_id, pengguna_id = produk.id, pemilik.id
    sesi.commit()

    mulai = threading.Barrier(2)
    Buat = sessionmaker(bind=mesin_uji, autoflush=False, expire_on_commit=False)

    def tambah_sepuluh() -> None:
        with Buat() as s:
            mulai.wait(timeout=10)  # pastikan keduanya benar-benar berbarengan
            catat_mutasi(s, produk_id, TipeMutasi.pembelian, Decimal("10"), pengguna_id)
            s.commit()

    utas = [threading.Thread(target=tambah_sepuluh) for _ in range(2)]
    for u in utas:
        u.start()
    for u in utas:
        u.join(timeout=20)

    with Buat() as s:
        saldo = sorted(m.saldo_sesudah for m in kartu_stok(s, produk_id))
        akhir = s.get(Produk, produk_id)
        assert akhir is not None
        assert saldo == [Decimal("10"), Decimal("20")], (
            f"saldo bertumpuk: {saldo}. Penguncian baris tidak bekerja."
        )
        assert akhir.stok == Decimal("20")
        assert periksa_keselarasan(s) == []
