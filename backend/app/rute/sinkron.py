from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.basisdata import ambil_sesi
from app.keamanan.hak_akses import pengguna_berjalan
from app.model.kategori import Kategori
from app.model.pengguna import Pengguna, Peran
from app.model.produk import Produk
from app.skema.produk import KategoriKeluar, ProdukKeluar, ProdukKeluarKasir

rute = APIRouter(prefix="/sinkron", tags=["sinkron"])


@rute.get("/katalog")
def katalog(
    sejak: datetime | None = None,
    batas: int = Query(default=1000, le=5000),
    sesi: Session = Depends(ambil_sesi),
    pengguna: Pengguna = Depends(pengguna_berjalan),
) -> dict[str, Any]:
    """Mengembalikan hanya yang berubah sejak waktu tertentu.

    Kolom hpp disaring untuk peran kasir, sama seperti di endpoint produk.
    Ini endpoint yang paling sering dipanggil perangkat kasir, sehingga
    kelalaian di sini membocorkan harga modal lewat pintu paling ramai
    (bab 07 §7.3).

    Tidak ada daftar penghapusan yang perlu dikirim: sistem ini tidak
    pernah menghapus data, produk hanya dinonaktifkan lewat kolom aktif,
    dan penonaktifan sampai sebagai perubahan biasa (bab 05 §5.4).
    """
    waktu_server = datetime.now(UTC)

    kueri_produk = select(Produk).order_by(Produk.diubah_pada).limit(batas)
    kueri_kategori = select(Kategori).order_by(Kategori.diubah_pada).limit(batas)
    if sejak is not None:
        kueri_produk = kueri_produk.where(Produk.diubah_pada > sejak)
        kueri_kategori = kueri_kategori.where(Kategori.diubah_pada > sejak)

    produk = list(sesi.execute(kueri_produk).scalars())
    bentuk = ProdukKeluar if pengguna.peran is Peran.pemilik else ProdukKeluarKasir

    return {
        "produk": [bentuk.model_validate(p).model_dump(mode="json") for p in produk],
        "kategori": [
            KategoriKeluar.model_validate(k).model_dump(mode="json")
            for k in sesi.execute(kueri_kategori).scalars()
        ],
        # Perangkat menyimpan waktu SERVER sebagai penanda sinkron
        # berikutnya, bukan jamnya sendiri. Jam komputer toko bisa meleset
        # berhari-hari, dan penanda yang salah membuat perubahan katalog
        # terlewat diam-diam (bab 05 §5.4).
        #
        # Ditulis berakhiran Z, bukan +00:00. Tanda + di dalam alamat URL
        # diuraikan sebagai spasi, sehingga perangkat yang mengirim balik
        # penanda apa adanya akan selalu ditolak. Z tidak punya arti khusus
        # di URL, sehingga penanda ini aman dipakai ulang tanpa disandikan.
        "waktu_server": waktu_server.isoformat().replace("+00:00", "Z"),
    }
