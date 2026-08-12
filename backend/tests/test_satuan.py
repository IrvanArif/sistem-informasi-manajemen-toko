from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.kesalahan import KesalahanDomain
from app.layanan.satuan import dari_satuan_dasar, ke_satuan_dasar, periksa_satuan
from app.model.produk import SatuanProduk


def satuan(nama: str, faktor: str, dasar: bool = False) -> SatuanProduk:
    return SatuanProduk(
        nama=nama, faktor=Decimal(faktor), harga_jual=1, is_dasar=dasar
    )


def test_satu_dus_menjadi_empat_puluh_bungkus() -> None:
    assert ke_satuan_dasar(Decimal("1"), Decimal("40")) == Decimal("40")


def test_tiga_bungkus_tetap_tiga() -> None:
    assert ke_satuan_dasar(Decimal("3"), Decimal("1")) == Decimal("3")


def test_barang_curah_berdesimal() -> None:
    """Beras 1,5 kg. Angka pecahan tidak boleh dibulatkan diam-diam."""
    assert ke_satuan_dasar(Decimal("1.5"), Decimal("1")) == Decimal("1.5")


def test_satu_karung_beras_menjadi_dua_puluh_lima_kilogram() -> None:
    assert ke_satuan_dasar(Decimal("1"), Decimal("25")) == Decimal("25")


def test_arah_sebaliknya() -> None:
    assert dari_satuan_dasar(Decimal("40"), Decimal("40")) == Decimal("1")


def test_satuan_dasar_wajib_ada() -> None:
    with pytest.raises(KesalahanDomain) as e:
        periksa_satuan([satuan("dus", "40")])
    assert e.value.kode == "SATUAN_DASAR_TUNGGAL"


def test_satuan_dasar_wajib_tepat_satu() -> None:
    with pytest.raises(KesalahanDomain) as e:
        periksa_satuan([satuan("bungkus", "1", True), satuan("dus", "40", True)])
    assert e.value.kode == "SATUAN_DASAR_TUNGGAL"


def test_satuan_dasar_wajib_berfaktor_satu() -> None:
    with pytest.raises(KesalahanDomain) as e:
        periksa_satuan([satuan("dus", "40", True)])
    assert e.value.kode == "FAKTOR_DASAR_HARUS_SATU"


def test_faktor_nol_ditolak() -> None:
    with pytest.raises(KesalahanDomain) as e:
        periksa_satuan([satuan("bungkus", "1", True), satuan("rusak", "0")])
    assert e.value.kode == "SATUAN_FAKTOR_TIDAK_SAH"


def test_nama_satuan_berulang_ditolak() -> None:
    with pytest.raises(KesalahanDomain) as e:
        periksa_satuan(
            [satuan("bungkus", "1", True), satuan("dus", "40"), satuan("dus", "24")]
        )
    assert e.value.kode == "NAMA_SATUAN_GANDA"


def test_daftar_kosong_ditolak() -> None:
    with pytest.raises(KesalahanDomain) as e:
        periksa_satuan([])
    assert e.value.kode == "SATUAN_KOSONG"


def test_susunan_sah_diterima() -> None:
    periksa_satuan([satuan("bungkus", "1", True), satuan("dus", "40")])


def test_pesan_menyebut_apa_itu_satuan_dasar() -> None:
    """Pesan menuntun, bukan sekadar menolak (bab 09 §9.5)."""
    with pytest.raises(KesalahanDomain) as e:
        periksa_satuan([satuan("dus", "40")])
    assert "terkecil" in e.value.pesan


@given(
    jumlah=st.decimals(min_value=Decimal("0.001"), max_value=Decimal("9999"), places=3),
    faktor=st.decimals(min_value=Decimal("0.001"), max_value=Decimal("1000"), places=3),
)
def test_konversi_bolak_balik_kembali_ke_asal(jumlah: Decimal, faktor: Decimal) -> None:
    """Sifat yang harus selalu benar, bukan hanya untuk contoh pilihan manusia.

    Contoh yang dipilih manusia cenderung terlalu rapi. Hypothesis
    membangkitkan ribuan kombinasi, termasuk yang tidak terpikirkan.
    """
    assert dari_satuan_dasar(ke_satuan_dasar(jumlah, faktor), faktor) == jumlah


@given(
    a=st.decimals(min_value=Decimal("0"), max_value=Decimal("999"), places=3),
    b=st.decimals(min_value=Decimal("0"), max_value=Decimal("999"), places=3),
    faktor=st.decimals(min_value=Decimal("0.001"), max_value=Decimal("100"), places=3),
)
def test_konversi_menjaga_penjumlahan(a: Decimal, b: Decimal, faktor: Decimal) -> None:
    """Mengubah lalu menjumlah sama dengan menjumlah lalu mengubah."""
    assert ke_satuan_dasar(a, faktor) + ke_satuan_dasar(b, faktor) == ke_satuan_dasar(
        a + b, faktor
    )
