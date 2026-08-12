from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.keamanan.sandi import hash_sandi
from app.kesalahan import KesalahanDomain
from app.layanan.produk import (
    buat_kategori,
    buat_produk,
    cari_produk,
    sesuaikan_stok,
    tambah_cepat,
    tambah_satuan,
    ubah_produk,
)
from app.layanan.stok import kartu_stok, periksa_keselarasan
from app.model.mutasi import TipeMutasi
from app.model.pengguna import Pengguna, Peran
from app.skema.produk import ProdukKilat, ProdukMasuk, ProdukUbah, SatuanMasuk


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


def indomie(stok_awal: str = "0") -> ProdukMasuk:
    """Indomie: satu produk, dua satuan, harga tiap satuan berdiri sendiri."""
    return ProdukMasuk(
        kode="P001",
        nama="Indomie Goreng",
        satuan_dasar="bungkus",
        stok_awal=Decimal(stok_awal),
        satuan=[
            SatuanMasuk(nama="bungkus", faktor=Decimal("1"), harga_jual=3500,
                        barcode="8991002101234", is_dasar=True),
            SatuanMasuk(nama="dus", faktor=Decimal("40"), harga_jual=130_000,
                        barcode="8991002109999"),
        ],
    )


def test_buat_produk_dengan_dua_satuan(sesi: Session, pemilik: Pengguna) -> None:
    p = buat_produk(sesi, indomie(), pemilik.id)
    assert {s.nama for s in p.satuan} == {"bungkus", "dus"}
    assert next(s for s in p.satuan if s.is_dasar).nama == "bungkus"


def test_harga_dus_bukan_kelipatan_harga_bungkus(
    sesi: Session, pemilik: Pengguna
) -> None:
    """Selisihnya disengaja, dan justru itulah alasan orang beli per dus."""
    p = buat_produk(sesi, indomie(), pemilik.id)
    harga = {s.nama: s.harga_jual for s in p.satuan}
    assert harga["dus"] == 130_000
    assert harga["bungkus"] * 40 == 140_000


def test_stok_awal_tercatat_sebagai_mutasi(sesi: Session, pemilik: Pengguna) -> None:
    """Bukan angka yang ditempel ke kolom stok, melainkan baris buku besar."""
    p = buat_produk(sesi, indomie("80"), pemilik.id)
    mutasi = kartu_stok(sesi, p.id)
    assert len(mutasi) == 1
    assert mutasi[0].tipe is TipeMutasi.stok_awal
    assert mutasi[0].jumlah == Decimal("80")
    assert p.stok == Decimal("80")
    assert periksa_keselarasan(sesi) == []


def test_produk_tanpa_stok_awal_tidak_menulis_mutasi(
    sesi: Session, pemilik: Pengguna
) -> None:
    p = buat_produk(sesi, indomie(), pemilik.id)
    assert kartu_stok(sesi, p.id) == []


def test_kode_ganda_ditolak(sesi: Session, pemilik: Pengguna) -> None:
    buat_produk(sesi, indomie(), pemilik.id)
    with pytest.raises(KesalahanDomain) as e:
        buat_produk(sesi, indomie(), pemilik.id)
    assert e.value.kode == "KODE_TERPAKAI"


def test_barcode_ganda_ditolak_dengan_pesan_menyebut_pemakainya(
    sesi: Session, pemilik: Pengguna
) -> None:
    buat_produk(sesi, indomie(), pemilik.id)
    lain = indomie()
    lain.kode = "P002"
    lain.nama = "Produk Lain"
    with pytest.raises(KesalahanDomain) as e:
        buat_produk(sesi, lain, pemilik.id)
    assert e.value.kode == "BARCODE_TERPAKAI"
    assert "Indomie" in e.value.pesan


def test_tanpa_satuan_dasar_ditolak(sesi: Session, pemilik: Pengguna) -> None:
    data = indomie()
    for s in data.satuan:
        s.is_dasar = False
    with pytest.raises(KesalahanDomain) as e:
        buat_produk(sesi, data, pemilik.id)
    assert e.value.kode == "SATUAN_DASAR_TUNGGAL"


def test_cari_lewat_barcode_langsung_menemukan_satu(
    sesi: Session, pemilik: Pengguna
) -> None:
    buat_produk(sesi, indomie(), pemilik.id)
    hasil = cari_produk(sesi, "8991002109999")
    assert [p.nama for p in hasil] == ["Indomie Goreng"]


def test_cari_lewat_kode(sesi: Session, pemilik: Pengguna) -> None:
    buat_produk(sesi, indomie(), pemilik.id)
    assert [p.kode for p in cari_produk(sesi, "P001")] == ["P001"]


def test_cari_lewat_nama_sebagian(sesi: Session, pemilik: Pengguna) -> None:
    buat_produk(sesi, indomie(), pemilik.id)
    assert len(cari_produk(sesi, "indomie")) == 1
    assert len(cari_produk(sesi, "GORENG")) == 1


def test_barcode_didahulukan_atas_nama(sesi: Session, pemilik: Pengguna) -> None:
    """Pindaian barcode tidak boleh menghasilkan daftar pilihan."""
    buat_produk(sesi, indomie(), pemilik.id)
    lain = indomie()
    lain.kode = "P002"
    lain.nama = "Indomie Soto"
    lain.satuan = [
        SatuanMasuk(nama="bungkus", faktor=Decimal("1"), harga_jual=3500,
                    barcode="8991002100000", is_dasar=True)
    ]
    buat_produk(sesi, lain, pemilik.id)

    assert len(cari_produk(sesi, "indomie")) == 2
    assert [p.nama for p in cari_produk(sesi, "8991002100000")] == ["Indomie Soto"]


def test_cari_tanpa_kata_mengembalikan_semua_yang_aktif(
    sesi: Session, pemilik: Pengguna
) -> None:
    p = buat_produk(sesi, indomie(), pemilik.id)
    assert len(cari_produk(sesi, "")) == 1
    ubah_produk(sesi, p.id, ProdukUbah(aktif=False))
    assert cari_produk(sesi, "") == []


def test_tambah_satuan_baru(sesi: Session, pemilik: Pengguna) -> None:
    p = buat_produk(sesi, indomie(), pemilik.id)
    tambah_satuan(
        sesi, p.id, SatuanMasuk(nama="renteng", faktor=Decimal("10"), harga_jual=34_000)
    )
    sesi.refresh(p)
    assert len(p.satuan) == 3


def test_menambah_satuan_dasar_kedua_ditolak(sesi: Session, pemilik: Pengguna) -> None:
    p = buat_produk(sesi, indomie(), pemilik.id)
    with pytest.raises(KesalahanDomain) as e:
        tambah_satuan(
            sesi, p.id,
            SatuanMasuk(nama="satuan2", faktor=Decimal("1"), harga_jual=1, is_dasar=True),
        )
    assert e.value.kode == "SATUAN_DASAR_TUNGGAL"


def test_tambah_cepat_menandai_perlu_dilengkapi(
    sesi: Session, pemilik: Pengguna
) -> None:
    p = tambah_cepat(sesi, ProdukKilat(nama="Sabun Cuci", harga=12_000), pemilik.id)
    assert p.perlu_dilengkapi is True
    assert p.satuan_dasar == "pcs"
    assert p.satuan[0].harga_jual == 12_000
    assert p.stok == Decimal("0")


def test_tambah_cepat_dengan_uuid_sama_tidak_menggandakan(
    sesi: Session, pemilik: Pengguna
) -> None:
    """Satu barang kilat yang terjual di beberapa nota offline tetap satu."""
    u = uuid4()
    a = tambah_cepat(sesi, ProdukKilat(nama="Sabun", harga=12_000, uuid_klien=u), pemilik.id)
    b = tambah_cepat(sesi, ProdukKilat(nama="Sabun", harga=12_000, uuid_klien=u), pemilik.id)
    assert a.id == b.id
    assert len(cari_produk(sesi, "")) == 1


def test_tambah_cepat_tanpa_uuid_selalu_produk_baru(
    sesi: Session, pemilik: Pengguna
) -> None:
    tambah_cepat(sesi, ProdukKilat(nama="Sabun", harga=12_000), pemilik.id)
    tambah_cepat(sesi, ProdukKilat(nama="Sabun", harga=12_000), pemilik.id)
    assert len(cari_produk(sesi, "")) == 2


def test_penyesuaian_stok_menulis_mutasi_beralasan(
    sesi: Session, pemilik: Pengguna
) -> None:
    p = buat_produk(sesi, indomie("80"), pemilik.id)
    sesuaikan_stok(sesi, p.id, Decimal("-3"), "rusak kena air", pemilik.id)
    sesi.refresh(p)
    assert p.stok == Decimal("77")
    terakhir = kartu_stok(sesi, p.id)[-1]
    assert terakhir.tipe is TipeMutasi.penyesuaian
    assert terakhir.alasan == "rusak kena air"


def test_kategori_ganda_ditolak(sesi: Session) -> None:
    buat_kategori(sesi, "Sembako")
    with pytest.raises(KesalahanDomain) as e:
        buat_kategori(sesi, "Sembako")
    assert e.value.kode == "KATEGORI_TERPAKAI"


def test_satu_dus_setara_empat_puluh_bungkus_di_stok(
    sesi: Session, pemilik: Pengguna
) -> None:
    """Contoh dari bab 03: jual satu dus, stok berkurang 40 bungkus."""
    p = buat_produk(sesi, indomie("120"), pemilik.id)
    dus = next(s for s in p.satuan if s.nama == "dus")
    sesuaikan_stok(sesi, p.id, -(Decimal("1") * dus.faktor), "jual 1 dus", pemilik.id)
    sesi.refresh(p)
    assert p.stok == Decimal("80")
