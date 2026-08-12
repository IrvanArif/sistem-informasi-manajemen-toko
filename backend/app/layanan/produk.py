from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.kesalahan import KesalahanDomain
from app.layanan.satuan import periksa_satuan
from app.layanan.stok import catat_mutasi
from app.model.kategori import Kategori
from app.model.mutasi import TipeMutasi
from app.model.produk import Produk, SatuanProduk
from app.skema.produk import ProdukKilat, ProdukMasuk, ProdukUbah, SatuanMasuk

NOL = Decimal("0")


def _pastikan_kode_bebas(sesi: Session, kode: str) -> None:
    ada = sesi.execute(
        select(Produk).where(Produk.kode == kode)
    ).scalar_one_or_none()
    if ada is not None:
        raise KesalahanDomain(
            "KODE_TERPAKAI",
            f"Kode {kode} sudah dipakai produk {ada.nama}. Pilih kode lain.",
            detail={"kode": kode},
        )


def _pastikan_barcode_bebas(sesi: Session, barcode: str, kecuali_id: int | None = None) -> None:
    kueri = select(SatuanProduk).where(SatuanProduk.barcode == barcode)
    if kecuali_id is not None:
        kueri = kueri.where(SatuanProduk.id != kecuali_id)
    ada = sesi.execute(kueri).scalar_one_or_none()
    if ada is not None:
        raise KesalahanDomain(
            "BARCODE_TERPAKAI",
            f"Barcode {barcode} sudah dipakai {ada.produk.nama} satuan {ada.nama}",
            detail={"barcode": barcode},
        )


def _bangun_satuan(data: list[SatuanMasuk]) -> list[SatuanProduk]:
    return [
        SatuanProduk(
            nama=s.nama,
            faktor=s.faktor,
            harga_jual=s.harga_jual,
            barcode=s.barcode or None,
            is_dasar=s.is_dasar,
        )
        for s in data
    ]


def buat_produk(sesi: Session, data: ProdukMasuk, pengguna_id: int) -> Produk:
    _pastikan_kode_bebas(sesi, data.kode)
    for s in data.satuan:
        if s.barcode:
            _pastikan_barcode_bebas(sesi, s.barcode)

    satuan = _bangun_satuan(data.satuan)
    periksa_satuan(satuan)

    produk = Produk(
        kode=data.kode,
        nama=data.nama,
        kategori_id=data.kategori_id,
        satuan_dasar=data.satuan_dasar,
        stok_minimum=data.stok_minimum,
        satuan=satuan,
    )
    sesi.add(produk)
    sesi.flush()

    # Stok awal ditulis sebagai mutasi, bukan sebagai angka yang langsung
    # ditempelkan ke kolom stok. Dengan begitu asal-usul setiap butir stok
    # selalu bisa ditelusuri sejak baris pertamanya.
    if data.stok_awal != NOL:
        catat_mutasi(
            sesi, produk.id, TipeMutasi.stok_awal, data.stok_awal, pengguna_id
        )

    sesi.commit()
    return produk


def ubah_produk(sesi: Session, produk_id: int, data: ProdukUbah) -> Produk:
    produk = ambil_produk(sesi, produk_id)
    for kolom in ("nama", "kategori_id", "stok_minimum", "perlu_dilengkapi", "aktif"):
        nilai = getattr(data, kolom)
        if nilai is not None:
            setattr(produk, kolom, nilai)
    sesi.commit()
    return produk


def ambil_produk(sesi: Session, produk_id: int) -> Produk:
    produk = sesi.get(Produk, produk_id)
    if produk is None:
        raise KesalahanDomain(
            "PRODUK_TIDAK_DITEMUKAN", "Produk tidak ditemukan", status=404
        )
    return produk


def tambah_satuan(sesi: Session, produk_id: int, data: SatuanMasuk) -> SatuanProduk:
    produk = ambil_produk(sesi, produk_id)
    if data.barcode:
        _pastikan_barcode_bebas(sesi, data.barcode)

    satuan = SatuanProduk(
        produk_id=produk.id,
        nama=data.nama,
        faktor=data.faktor,
        harga_jual=data.harga_jual,
        barcode=data.barcode or None,
        is_dasar=data.is_dasar,
    )
    periksa_satuan([*produk.satuan, satuan])
    sesi.add(satuan)
    sesi.commit()
    return satuan


def cari_produk(
    sesi: Session,
    kata: str = "",
    kategori_id: int | None = None,
    aktif: bool | None = True,
    perlu_dilengkapi: bool | None = None,
    batas: int = 50,
) -> list[Produk]:
    """Urutan pencocokan mengikuti bab 04: barcode, kode, lalu nama.

    Urutannya bukan selera. Pindaian barcode harus langsung menemukan satu
    barang tanpa pilihan, sementara pencarian nama boleh mengembalikan
    banyak. Mendahulukan nama akan membuat scanner menampilkan daftar
    pilihan, dan kasir kehilangan waktu justru di saat paling sibuk.
    """
    dasar = select(Produk)
    if aktif is not None:
        dasar = dasar.where(Produk.aktif.is_(aktif))
    if kategori_id is not None:
        dasar = dasar.where(Produk.kategori_id == kategori_id)
    if perlu_dilengkapi is not None:
        dasar = dasar.where(Produk.perlu_dilengkapi.is_(perlu_dilengkapi))

    kata = kata.strip()
    if not kata:
        return list(sesi.execute(dasar.order_by(Produk.nama).limit(batas)).scalars())

    lewat_barcode = dasar.join(SatuanProduk).where(SatuanProduk.barcode == kata)
    hasil = list(sesi.execute(lewat_barcode.limit(batas)).scalars())
    if hasil:
        return hasil

    hasil = list(sesi.execute(dasar.where(Produk.kode == kata).limit(batas)).scalars())
    if hasil:
        return hasil

    lewat_nama = dasar.where(Produk.nama.ilike(f"%{kata}%")).order_by(Produk.nama)
    return list(sesi.execute(lewat_nama.limit(batas)).scalars())


def tambah_cepat(sesi: Session, data: ProdukKilat, pengguna_id: int) -> Produk:
    """Menambah barang di tengah transaksi, dengan nama dan harga saja.

    Tanpa jalan pintas ini, kasir yang menemukan barang tak terdaftar
    harus berhenti melayani untuk mengisi form katalog lengkap, dan sistem
    akan ditinggalkan di minggu pertama (STK-05).
    """
    if data.uuid_klien is not None:
        ada = sesi.execute(
            select(Produk).where(Produk.uuid_klien == data.uuid_klien)
        ).scalar_one_or_none()
        # Barang yang sama, ditambahkan kilat sekali lalu terjual di
        # beberapa nota offline, tetap menghasilkan satu produk (bab 05).
        if ada is not None:
            return ada

    kode = _kode_kilat_berikutnya(sesi)
    produk = Produk(
        kode=kode,
        nama=data.nama,
        satuan_dasar="pcs",
        perlu_dilengkapi=True,
        uuid_klien=data.uuid_klien,
        satuan=[
            SatuanProduk(
                nama="pcs", faktor=Decimal("1"), harga_jual=data.harga, is_dasar=True
            )
        ],
    )
    sesi.add(produk)
    sesi.commit()
    return produk


def _kode_kilat_berikutnya(sesi: Session) -> str:
    jumlah = int(
        sesi.execute(
            select(func.count()).select_from(Produk).where(Produk.kode.like("KILAT-%"))
        ).scalar_one()
    )
    return f"KILAT-{jumlah + 1:04d}"


def daftar_kategori(sesi: Session) -> list[Kategori]:
    return list(sesi.execute(select(Kategori).order_by(Kategori.nama)).scalars())


def buat_kategori(sesi: Session, nama: str) -> Kategori:
    ada = sesi.execute(
        select(Kategori).where(Kategori.nama == nama)
    ).scalar_one_or_none()
    if ada is not None:
        raise KesalahanDomain(
            "KATEGORI_TERPAKAI", f"Kategori {nama} sudah ada", detail={"nama": nama}
        )
    kategori = Kategori(nama=nama)
    sesi.add(kategori)
    sesi.commit()
    return kategori


def sesuaikan_stok(
    sesi: Session, produk_id: int, jumlah: Decimal, alasan: str, pengguna_id: int
) -> Produk:
    catat_mutasi(
        sesi, produk_id, TipeMutasi.penyesuaian, jumlah, pengguna_id, alasan=alasan
    )
    sesi.commit()
    return ambil_produk(sesi, produk_id)


def cari_dengan_uuid(sesi: Session, uuid_klien: UUID) -> Produk | None:
    return sesi.execute(
        select(Produk).where(Produk.uuid_klien == uuid_klien)
    ).scalar_one_or_none()
