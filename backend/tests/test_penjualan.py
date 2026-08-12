from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.keamanan.sandi import hash_sandi
from app.kesalahan import KesalahanDomain
from app.layanan.kas import buka_sesi, hitung_kas_sistem, tutup_sesi
from app.layanan.penjualan import catat_penjualan
from app.layanan.produk import buat_produk
from app.layanan.stok import periksa_keselarasan
from app.model.pengguna import Pengguna, Peran
from app.model.produk import Produk
from app.skema.penjualan import ItemMasuk, PenjualanMasuk
from app.skema.produk import ProdukKilat, ProdukMasuk, SatuanMasuk


@pytest.fixture
def kasir(sesi: Session) -> Pengguna:
    p = Pengguna(nama_pengguna="kasir1", nama_lengkap="Kasir Satu",
                 sandi_hash=hash_sandi("rahasia123"), peran=Peran.kasir)
    sesi.add(p)
    sesi.commit()
    return p


@pytest.fixture
def indomie(sesi: Session, kasir: Pengguna) -> Produk:
    return buat_produk(
        sesi,
        ProdukMasuk(
            kode="P001", nama="Indomie Goreng", satuan_dasar="bungkus",
            stok_awal=Decimal("120"),
            satuan=[
                SatuanMasuk(nama="bungkus", faktor=Decimal("1"), harga_jual=3500,
                            is_dasar=True),
                SatuanMasuk(nama="dus", faktor=Decimal("40"), harga_jual=130_000),
            ],
        ),
        kasir.id,
    )


def nota(indomie: Produk, satuan_nama: str, jumlah: str, harga: int) -> PenjualanMasuk:
    satuan = next(s for s in indomie.satuan if s.nama == satuan_nama)
    sub = int(harga * Decimal(jumlah))
    return PenjualanMasuk(
        uuid_klien=uuid4(),
        nomor_nota=f"20260811-K1-{uuid4().hex[:4]}",
        waktu_transaksi=datetime.now(UTC),
        total=sub,
        dibayar=sub,
        kembalian=0,
        item=[
            ItemMasuk(produk_id=indomie.id, satuan_id=satuan.id,
                      jumlah=Decimal(jumlah), harga_satuan=harga, subtotal=sub)
        ],
    )


def test_transaksi_memotong_stok(sesi: Session, kasir: Pengguna, indomie: Produk) -> None:
    buka_sesi(sesi, kasir.id, 100_000)
    catat_penjualan(sesi, nota(indomie, "bungkus", "3", 3500), kasir.id)
    sesi.refresh(indomie)
    assert indomie.stok == Decimal("117")
    assert periksa_keselarasan(sesi) == []


def test_jual_satu_dus_memotong_empat_puluh_bungkus(
    sesi: Session, kasir: Pengguna, indomie: Produk
) -> None:
    """Inti satuan bertingkat, diuji lewat jalur penjualan sungguhan."""
    buka_sesi(sesi, kasir.id, 100_000)
    catat_penjualan(sesi, nota(indomie, "dus", "1", 130_000), kasir.id)
    sesi.refresh(indomie)
    assert indomie.stok == Decimal("80")


def test_baris_nota_menyimpan_salinan(
    sesi: Session, kasir: Pengguna, indomie: Produk
) -> None:
    """Laba historis tidak boleh berubah saat harga hari ini berubah."""
    buka_sesi(sesi, kasir.id, 100_000)
    n, _ = catat_penjualan(sesi, nota(indomie, "dus", "1", 130_000), kasir.id)
    baris = n.item[0]
    assert baris.nama_produk == "Indomie Goreng"
    assert baris.nama_satuan == "dus"
    assert baris.faktor == Decimal("40")
    assert baris.jumlah_dasar == Decimal("40")

    indomie.nama = "Nama Berubah"
    sesi.commit()
    sesi.refresh(baris)
    assert baris.nama_produk == "Indomie Goreng"


def test_uuid_sama_tidak_menggandakan(
    sesi: Session, kasir: Pengguna, indomie: Produk
) -> None:
    """Pengiriman ulang setelah jaringan putus tidak boleh menggandakan omzet."""
    buka_sesi(sesi, kasir.id, 100_000)
    data = nota(indomie, "bungkus", "3", 3500)

    pertama, baru1 = catat_penjualan(sesi, data, kasir.id)
    kedua, baru2 = catat_penjualan(sesi, data, kasir.id)

    assert baru1 is True
    assert baru2 is False
    assert pertama.id == kedua.id
    sesi.refresh(indomie)
    assert indomie.stok == Decimal("117")  # dipotong sekali saja


def test_nomor_nota_ganda_ditolak(
    sesi: Session, kasir: Pengguna, indomie: Produk
) -> None:
    buka_sesi(sesi, kasir.id, 100_000)
    a = nota(indomie, "bungkus", "1", 3500)
    catat_penjualan(sesi, a, kasir.id)

    b = nota(indomie, "bungkus", "1", 3500)
    b.nomor_nota = a.nomor_nota
    with pytest.raises(KesalahanDomain) as e:
        catat_penjualan(sesi, b, kasir.id)
    assert e.value.kode == "NOTA_GANDA"


def test_subtotal_yang_dikirim_salah_ditolak(
    sesi: Session, kasir: Pengguna, indomie: Produk
) -> None:
    """Penjumlahan tidak boleh dipercayakan ke perangkat."""
    buka_sesi(sesi, kasir.id, 100_000)
    data = nota(indomie, "bungkus", "3", 3500)
    data.item[0].subtotal = 1
    data.total = 1
    with pytest.raises(KesalahanDomain) as e:
        catat_penjualan(sesi, data, kasir.id)
    assert e.value.kode == "TOTAL_TIDAK_COCOK"


def test_total_nota_yang_dikirim_salah_ditolak(
    sesi: Session, kasir: Pengguna, indomie: Produk
) -> None:
    buka_sesi(sesi, kasir.id, 100_000)
    data = nota(indomie, "bungkus", "3", 3500)
    data.total = 999_999
    with pytest.raises(KesalahanDomain) as e:
        catat_penjualan(sesi, data, kasir.id)
    assert e.value.kode == "TOTAL_TIDAK_COCOK"


def test_tanpa_sesi_kas_ditolak(
    sesi: Session, kasir: Pengguna, indomie: Produk
) -> None:
    with pytest.raises(KesalahanDomain) as e:
        catat_penjualan(sesi, nota(indomie, "bungkus", "1", 3500), kasir.id)
    assert e.value.kode == "SESI_KAS_BELUM_DIBUKA"


def test_barang_curah_berdesimal(sesi: Session, kasir: Pengguna) -> None:
    beras = buat_produk(
        sesi,
        ProdukMasuk(kode="P002", nama="Beras", satuan_dasar="kg",
                    stok_awal=Decimal("42.5"),
                    satuan=[SatuanMasuk(nama="kg", faktor=Decimal("1"),
                                        harga_jual=14_000, is_dasar=True)]),
        kasir.id,
    )
    buka_sesi(sesi, kasir.id, 100_000)
    catat_penjualan(sesi, nota(beras, "kg", "1.5", 14_000), kasir.id)
    sesi.refresh(beras)
    assert beras.stok == Decimal("41.000")


def test_tambah_cepat_di_dalam_nota(sesi: Session, kasir: Pengguna) -> None:
    """Barang tak terdaftar bisa dijual tanpa menghentikan antrean."""
    buka_sesi(sesi, kasir.id, 100_000)
    u = uuid4()
    data = PenjualanMasuk(
        uuid_klien=uuid4(), nomor_nota="20260811-K1-9001",
        waktu_transaksi=datetime.now(UTC), total=12_000, dibayar=12_000, kembalian=0,
        item=[ItemMasuk(produk_baru=ProdukKilat(nama="Sabun", harga=12_000, uuid_klien=u),
                        jumlah=Decimal("1"), harga_satuan=12_000, subtotal=12_000)],
    )
    n, _ = catat_penjualan(sesi, data, kasir.id)
    assert n.item[0].nama_produk == "Sabun"
    # Stok menjadi minus, dicatat bukan dihalangi (ADR-0006)
    assert n.item[0].jumlah_dasar == Decimal("1")


def test_hpp_diambil_pada_waktu_transaksi(
    sesi: Session, kasir: Pengguna, indomie: Produk
) -> None:
    """Nota offline yang baru sampai tidak boleh memakai HPP sekarang."""
    buka_sesi(sesi, kasir.id, 100_000)
    indomie.hpp = Decimal("2866.6667")
    sesi.commit()

    data = nota(indomie, "bungkus", "1", 3500)
    data.waktu_transaksi = datetime.now(UTC) - timedelta(hours=5)
    n, _ = catat_penjualan(sesi, data, kasir.id)
    assert n.item[0].hpp_saat_itu >= Decimal("0")


def test_kas_sistem_menjumlahkan_penjualan_tunai(
    sesi: Session, kasir: Pengguna, indomie: Produk
) -> None:
    kas = buka_sesi(sesi, kasir.id, 100_000)
    catat_penjualan(sesi, nota(indomie, "bungkus", "3", 3500), kasir.id)
    assert hitung_kas_sistem(sesi, kas) == 100_000 + 10_500


def test_tutup_sesi_dengan_selisih_menuntut_catatan(
    sesi: Session, kasir: Pengguna, indomie: Produk
) -> None:
    kas = buka_sesi(sesi, kasir.id, 100_000)
    catat_penjualan(sesi, nota(indomie, "bungkus", "3", 3500), kasir.id)
    with pytest.raises(KesalahanDomain) as e:
        tutup_sesi(sesi, kas.id, 110_000, None, kasir.id)
    assert e.value.kode == "SELISIH_KAS_BUTUH_CATATAN"


def test_tutup_sesi_tanpa_selisih_tidak_menuntut_catatan(
    sesi: Session, kasir: Pengguna, indomie: Produk
) -> None:
    kas = buka_sesi(sesi, kasir.id, 100_000)
    catat_penjualan(sesi, nota(indomie, "bungkus", "3", 3500), kasir.id)
    hasil = tutup_sesi(sesi, kas.id, 110_500, None, kasir.id)
    assert hasil.selisih == 0
    assert hasil.status.value == "tertutup"


def test_selisih_dicatat_apa_adanya(
    sesi: Session, kasir: Pengguna, indomie: Produk
) -> None:
    """Sistem tidak pernah membetulkan selisih."""
    kas = buka_sesi(sesi, kasir.id, 100_000)
    hasil = tutup_sesi(sesi, kas.id, 95_000, "uang hilang, dicari besok", kasir.id)
    assert hasil.selisih == -5_000
    assert hasil.kas_sistem == 100_000


def test_dua_sesi_terbuka_ditolak(sesi: Session, kasir: Pengguna) -> None:
    buka_sesi(sesi, kasir.id, 100_000)
    with pytest.raises(KesalahanDomain) as e:
        buka_sesi(sesi, kasir.id, 50_000)
    assert e.value.kode == "SESI_KAS_SUDAH_TERBUKA"
