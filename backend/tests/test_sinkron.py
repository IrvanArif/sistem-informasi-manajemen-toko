from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.keamanan.sandi import hash_sandi
from app.keamanan.token import terbitkan_token_akses
from app.layanan.produk import buat_produk
from app.model.pengguna import Pengguna, Peran
from app.skema.produk import ProdukMasuk, SatuanMasuk


def buat(sesi: Session, nama: str, peran: Peran) -> Pengguna:
    p = Pengguna(nama_pengguna=nama, nama_lengkap=nama.title(),
                 sandi_hash=hash_sandi("rahasia123"), peran=peran)
    sesi.add(p)
    sesi.commit()
    return p


def kepala(p: Pengguna) -> dict[str, str]:
    return {"Authorization": f"Bearer {terbitkan_token_akses(p.id, p.peran.value)}"}


@pytest.fixture
def pemilik(sesi: Session) -> Pengguna:
    return buat(sesi, "irvan", Peran.pemilik)


def produk(sesi: Session, kode: str, pengguna_id: int) -> None:
    buat_produk(
        sesi,
        ProdukMasuk(kode=kode, nama=f"Barang {kode}", satuan_dasar="pcs",
                    satuan=[SatuanMasuk(nama="pcs", faktor=Decimal("1"),
                                        harga_jual=1000, is_dasar=True)]),
        pengguna_id,
    )


def test_tanpa_sejak_mengembalikan_semua(klien: TestClient, sesi: Session,
                                          pemilik: Pengguna) -> None:
    produk(sesi, "P001", pemilik.id)
    produk(sesi, "P002", pemilik.id)
    j = klien.get("/api/v1/sinkron/katalog", headers=kepala(pemilik)).json()
    assert len(j["produk"]) == 2
    assert "waktu_server" in j


def test_dengan_sejak_hanya_yang_berubah(klien: TestClient, sesi: Session,
                                          pemilik: Pengguna) -> None:
    produk(sesi, "P001", pemilik.id)
    penanda = klien.get("/api/v1/sinkron/katalog",
                        headers=kepala(pemilik)).json()["waktu_server"]

    produk(sesi, "P002", pemilik.id)
    j = klien.get(f"/api/v1/sinkron/katalog?sejak={penanda}",
                  headers=kepala(pemilik)).json()
    assert [p["kode"] for p in j["produk"]] == ["P002"]


def test_tanpa_perubahan_mengembalikan_kosong(klien: TestClient, sesi: Session,
                                               pemilik: Pengguna) -> None:
    produk(sesi, "P001", pemilik.id)
    penanda = klien.get("/api/v1/sinkron/katalog",
                        headers=kepala(pemilik)).json()["waktu_server"]
    j = klien.get(f"/api/v1/sinkron/katalog?sejak={penanda}",
                  headers=kepala(pemilik)).json()
    assert j["produk"] == []


def test_kasir_tidak_menerima_hpp(klien: TestClient, sesi: Session,
                                   pemilik: Pengguna) -> None:
    """Endpoint paling ramai, jadi paling penting disaring."""
    produk(sesi, "P001", pemilik.id)
    kasir = buat(sesi, "kasir1", Peran.kasir)

    untuk_pemilik = klien.get("/api/v1/sinkron/katalog", headers=kepala(pemilik)).json()
    untuk_kasir = klien.get("/api/v1/sinkron/katalog", headers=kepala(kasir)).json()

    assert "hpp" in untuk_pemilik["produk"][0]
    assert "hpp" not in untuk_kasir["produk"][0]


def test_penonaktifan_sampai_sebagai_perubahan(klien: TestClient, sesi: Session,
                                                pemilik: Pengguna) -> None:
    """Tidak ada daftar penghapusan, karena data tidak pernah dihapus."""
    produk(sesi, "P001", pemilik.id)
    penanda = klien.get("/api/v1/sinkron/katalog",
                        headers=kepala(pemilik)).json()["waktu_server"]

    pid = klien.get("/api/v1/produk", headers=kepala(pemilik)).json()[0]["id"]
    klien.patch(f"/api/v1/produk/{pid}", json={"aktif": False}, headers=kepala(pemilik))

    j = klien.get(f"/api/v1/sinkron/katalog?sejak={penanda}",
                  headers=kepala(pemilik)).json()
    assert len(j["produk"]) == 1
    assert j["produk"][0]["aktif"] is False


def test_waktu_server_bergerak_maju(klien: TestClient, pemilik: Pengguna) -> None:
    a = klien.get("/api/v1/sinkron/katalog", headers=kepala(pemilik)).json()["waktu_server"]
    b = klien.get("/api/v1/sinkron/katalog", headers=kepala(pemilik)).json()["waktu_server"]
    assert datetime.fromisoformat(b) >= datetime.fromisoformat(a)
    assert datetime.fromisoformat(a) <= datetime.now(UTC) + timedelta(seconds=5)


def test_penanda_waktu_aman_dipakai_di_alamat_url(
    klien: TestClient, pemilik: Pengguna
) -> None:
    """Penanda harus bisa dikirim balik apa adanya, tanpa disandikan.

    Sebelum diperbaiki, waktu_server berakhir +00:00. Tanda + di dalam URL
    diuraikan sebagai spasi, sehingga perangkat yang mengirim balik penanda
    yang baru saja diterimanya selalu ditolak 422 dan sinkronisasi tidak
    pernah berjalan sama sekali.
    """
    penanda = klien.get("/api/v1/sinkron/katalog",
                        headers=kepala(pemilik)).json()["waktu_server"]
    assert penanda.endswith("Z")
    assert "+" not in penanda

    j = klien.get(f"/api/v1/sinkron/katalog?sejak={penanda}", headers=kepala(pemilik))
    assert j.status_code == 200
    assert "produk" in j.json()
