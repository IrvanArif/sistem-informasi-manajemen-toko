from decimal import Decimal

from app.kesalahan import KesalahanDomain
from app.model.produk import Produk, SatuanProduk

SATU = Decimal("1")


def ke_satuan_dasar(jumlah: Decimal, faktor: Decimal) -> Decimal:
    """Mengubah jumlah dalam satuan terpilih menjadi jumlah satuan dasar.

    Satu-satunya tempat perkalian ini terjadi. Menyebarkannya ke banyak
    tempat adalah cara paling pasti membuat stok berselisih, karena satu
    saja yang lupa mengalikan sudah cukup merusak seluruh saldo.
    """
    return jumlah * faktor


def dari_satuan_dasar(jumlah_dasar: Decimal, faktor: Decimal) -> Decimal:
    """Arah sebaliknya, untuk menampilkan stok dalam satuan pilihan."""
    return jumlah_dasar / faktor


def satuan_dasar_dari(produk: Produk) -> SatuanProduk:
    for s in produk.satuan:
        if s.is_dasar:
            return s
    raise KesalahanDomain(
        "SATUAN_DASAR_TIDAK_ADA",
        f"Produk {produk.nama} belum punya satuan dasar. Tambahkan satu lebih dulu.",
        detail={"produk": produk.nama},
    )


def cari_satuan(produk: Produk, satuan_id: int) -> SatuanProduk:
    for s in produk.satuan:
        if s.id == satuan_id:
            return s
    raise KesalahanDomain(
        "SATUAN_TIDAK_DITEMUKAN",
        f"Satuan yang dipilih bukan milik produk {produk.nama}",
        detail={"produk_id": produk.id, "satuan_id": satuan_id},
    )


def periksa_satuan(daftar: list[SatuanProduk]) -> None:
    """Menjaga aturan satuan sebelum apa pun disimpan.

    Dipanggil di layanan, bukan hanya diandalkan pada batasan basis data,
    supaya pesannya bisa menyebut apa yang salah dan apa yang harus
    dilakukan, bukan sekadar melanggar batasan.
    """
    if not daftar:
        raise KesalahanDomain(
            "SATUAN_KOSONG", "Produk harus punya sedikitnya satu satuan"
        )

    for s in daftar:
        if s.faktor <= 0:
            raise KesalahanDomain(
                "SATUAN_FAKTOR_TIDAK_SAH",
                "Faktor satuan harus lebih besar dari 0",
                detail={"satuan": s.nama, "faktor": str(s.faktor)},
            )

    dasar = [s for s in daftar if s.is_dasar]
    if len(dasar) != 1:
        raise KesalahanDomain(
            "SATUAN_DASAR_TUNGGAL",
            "Produk harus punya tepat satu satuan dasar, "
            f"ditemukan {len(dasar)}. Satuan dasar adalah yang terkecil, "
            "tempat stok dihitung.",
            detail={"jumlah_dasar": len(dasar)},
        )

    if dasar[0].faktor != SATU:
        raise KesalahanDomain(
            "FAKTOR_DASAR_HARUS_SATU",
            "Satuan dasar harus berfaktor 1, karena ia yang menjadi acuan "
            "bagi satuan lain",
            detail={"satuan": dasar[0].nama, "faktor": str(dasar[0].faktor)},
        )

    nama = [s.nama for s in daftar]
    if len(set(nama)) != len(nama):
        raise KesalahanDomain(
            "NAMA_SATUAN_GANDA",
            "Nama satuan tidak boleh berulang dalam satu produk",
        )
