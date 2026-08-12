from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.keamanan.sandi import hash_sandi
from app.keamanan.token import terbitkan_token_akses
from app.model.pengguna import Pengguna, Peran

SANDI = "rahasia123"

INDOMIE = {
    "kode": "P001",
    "nama": "Indomie Goreng",
    "satuan_dasar": "bungkus",
    "stok_awal": "120",
    "satuan": [
        {"nama": "bungkus", "faktor": "1", "harga_jual": 3500,
         "barcode": "8991002101234", "is_dasar": True},
        {"nama": "dus", "faktor": "40", "harga_jual": 130000,
         "barcode": "8991002109999", "is_dasar": False},
    ],
}


def buat(sesi: Session, nama: str, peran: Peran) -> Pengguna:
    p = Pengguna(nama_pengguna=nama, nama_lengkap=nama.title(),
                 sandi_hash=hash_sandi(SANDI), peran=peran)
    sesi.add(p)
    sesi.commit()
    return p


def kepala(p: Pengguna) -> dict[str, str]:
    return {"Authorization": f"Bearer {terbitkan_token_akses(p.id, p.peran.value)}"}


@pytest.fixture
def pemilik(sesi: Session) -> Pengguna:
    return buat(sesi, "irvan", Peran.pemilik)


@pytest.fixture
def kasir(sesi: Session) -> Pengguna:
    return buat(sesi, "kasir1", Peran.kasir)


def test_pemilik_membuat_produk(klien: TestClient, pemilik: Pengguna) -> None:
    j = klien.post("/api/v1/produk", json=INDOMIE, headers=kepala(pemilik))
    assert j.status_code == 201
    isi = j.json()
    assert isi["stok"] == "120.000"
    assert len(isi["satuan"]) == 2


def test_kasir_tidak_boleh_membuat_produk(
    klien: TestClient, pemilik: Pengguna, kasir: Pengguna
) -> None:
    j = klien.post("/api/v1/produk", json=INDOMIE, headers=kepala(kasir))
    assert j.status_code == 403
    assert j.json()["kode"] == "TIDAK_BERHAK"


def test_jawaban_untuk_kasir_tidak_memuat_hpp(
    klien: TestClient, pemilik: Pengguna, kasir: Pengguna
) -> None:
    """Harga modal adalah informasi dagang yang tidak perlu diketahui pegawai."""
    klien.post("/api/v1/produk", json=INDOMIE, headers=kepala(pemilik))

    untuk_pemilik = klien.get("/api/v1/produk", headers=kepala(pemilik)).json()
    untuk_kasir = klien.get("/api/v1/produk", headers=kepala(kasir)).json()

    assert "hpp" in untuk_pemilik[0]
    assert "hpp" not in untuk_kasir[0]


def test_satu_produk_juga_disaring_untuk_kasir(
    klien: TestClient, pemilik: Pengguna, kasir: Pengguna
) -> None:
    pid = klien.post("/api/v1/produk", json=INDOMIE, headers=kepala(pemilik)).json()["id"]
    assert "hpp" not in klien.get(f"/api/v1/produk/{pid}", headers=kepala(kasir)).json()


def test_jumlah_dikirim_sebagai_string(
    klien: TestClient, pemilik: Pengguna
) -> None:
    """Angka JSON adalah pecahan biner, string tidak kehilangan ketelitian."""
    j = klien.post("/api/v1/produk", json=INDOMIE, headers=kepala(pemilik)).json()
    assert isinstance(j["stok"], str)
    assert isinstance(j["satuan"][1]["faktor"], str)
    assert j["satuan"][1]["faktor"] == "40.000"


def test_cari_lewat_barcode(klien: TestClient, pemilik: Pengguna) -> None:
    klien.post("/api/v1/produk", json=INDOMIE, headers=kepala(pemilik))
    hasil = klien.get("/api/v1/produk?cari=8991002109999", headers=kepala(pemilik)).json()
    assert [p["nama"] for p in hasil] == ["Indomie Goreng"]


def test_kasir_boleh_tambah_cepat(klien: TestClient, kasir: Pengguna) -> None:
    """Dipakai di tengah antrean, jadi kasir harus boleh (STK-05)."""
    j = klien.post("/api/v1/produk/kilat",
                   json={"nama": "Sabun Cuci", "harga": 12000}, headers=kepala(kasir))
    assert j.status_code == 201
    assert j.json()["perlu_dilengkapi"] is True
    assert "hpp" not in j.json()


def test_penyesuaian_stok_menuntut_alasan(
    klien: TestClient, pemilik: Pengguna
) -> None:
    pid = klien.post("/api/v1/produk", json=INDOMIE, headers=kepala(pemilik)).json()["id"]
    j = klien.post("/api/v1/penyesuaian-stok",
                   json={"produk_id": pid, "jumlah": "-3", "alasan": ""},
                   headers=kepala(pemilik))
    assert j.status_code == 422


def test_penyesuaian_stok_berhasil(klien: TestClient, pemilik: Pengguna) -> None:
    pid = klien.post("/api/v1/produk", json=INDOMIE, headers=kepala(pemilik)).json()["id"]
    j = klien.post("/api/v1/penyesuaian-stok",
                   json={"produk_id": pid, "jumlah": "-40", "alasan": "jual satu dus"},
                   headers=kepala(pemilik))
    assert j.status_code == 200
    assert Decimal(j.json()["stok"]) == Decimal("80")


def test_kartu_stok_hanya_untuk_pemilik(
    klien: TestClient, pemilik: Pengguna, kasir: Pengguna
) -> None:
    pid = klien.post("/api/v1/produk", json=INDOMIE, headers=kepala(pemilik)).json()["id"]
    assert klien.get(f"/api/v1/produk/{pid}/kartu-stok",
                     headers=kepala(kasir)).status_code == 403
    kartu = klien.get(f"/api/v1/produk/{pid}/kartu-stok", headers=kepala(pemilik)).json()
    assert kartu[0]["tipe"] == "stok_awal"


def test_stok_minus_hanya_untuk_pemilik(
    klien: TestClient, pemilik: Pengguna, kasir: Pengguna
) -> None:
    assert klien.get("/api/v1/stok/minus", headers=kepala(kasir)).status_code == 403
    assert klien.get("/api/v1/stok/minus", headers=kepala(pemilik)).status_code == 200


def test_kategori_dibuat_lalu_terbaca(klien: TestClient, pemilik: Pengguna) -> None:
    assert klien.post("/api/v1/kategori", json={"nama": "Sembako"},
                      headers=kepala(pemilik)).status_code == 201
    assert [k["nama"] for k in
            klien.get("/api/v1/kategori", headers=kepala(pemilik)).json()] == ["Sembako"]


def test_barcode_ganda_ditolak_lewat_api(klien: TestClient, pemilik: Pengguna) -> None:
    klien.post("/api/v1/produk", json=INDOMIE, headers=kepala(pemilik))
    lain = {**INDOMIE, "kode": "P002", "nama": "Lain"}
    j = klien.post("/api/v1/produk", json=lain, headers=kepala(pemilik))
    assert j.status_code == 422
    assert j.json()["kode"] == "BARCODE_TERPAKAI"


def test_bentuk_angka_sama_baik_baru_dibuat_maupun_dibaca_ulang(
    klien: TestClient, pemilik: Pengguna
) -> None:
    """Bentuk jawaban tidak boleh bergantung dari mana objeknya datang.

    Sebelum angka desimalnya dipatok, produk yang baru dibuat mengirim
    faktor "40" sementara produk yang sama setelah dibaca ulang mengirim
    "40.000". Perbandingan di sisi browser jadi tidak bisa dipercaya.
    """
    baru = klien.post("/api/v1/produk", json=INDOMIE, headers=kepala(pemilik)).json()
    dibaca = klien.get(f"/api/v1/produk/{baru['id']}", headers=kepala(pemilik)).json()

    assert baru["stok"] == dibaca["stok"]
    assert baru["hpp"] == dibaca["hpp"]
    assert [s["faktor"] for s in baru["satuan"]] == [
        s["faktor"] for s in dibaca["satuan"]
    ]


def test_hpp_memakai_empat_angka_desimal(
    klien: TestClient, pemilik: Pengguna
) -> None:
    j = klien.post("/api/v1/produk", json=INDOMIE, headers=kepala(pemilik)).json()
    assert j["hpp"] == "0.0000"
    assert j["stok"] == "120.000"
