from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.keamanan.sandi import hash_sandi
from app.model.pengguna import Pengguna, Peran

SANDI = "rahasia123"


def pemilik(sesi: Session) -> Pengguna:
    p = Pengguna(
        nama_pengguna="irvan",
        nama_lengkap="Irvan",
        sandi_hash=hash_sandi(SANDI),
        peran=Peran.pemilik,
    )
    sesi.add(p)
    sesi.commit()
    return p


def masuk(klien: TestClient) -> dict[str, str]:
    jawaban = klien.post(
        "/api/v1/auth/masuk", json={"nama_pengguna": "irvan", "sandi": SANDI}
    )
    assert jawaban.status_code == 200
    return dict(jawaban.json())


def test_alur_masuk_lalu_saya(klien: TestClient, sesi: Session) -> None:
    pemilik(sesi)
    token = masuk(klien)["token_akses"]
    saya = klien.get("/api/v1/auth/saya", headers={"Authorization": f"Bearer {token}"})
    assert saya.status_code == 200
    assert saya.json()["nama_pengguna"] == "irvan"
    assert "sandi_hash" not in saya.json()


def test_sandi_salah_memberi_bentuk_kesalahan_seragam(
    klien: TestClient, sesi: Session
) -> None:
    pemilik(sesi)
    jawaban = klien.post(
        "/api/v1/auth/masuk", json={"nama_pengguna": "irvan", "sandi": "salah"}
    )
    assert jawaban.status_code == 401
    assert set(jawaban.json()) == {"kode", "pesan", "detail"}
    assert jawaban.json()["kode"] == "KREDENSIAL_SALAH"


def test_segarkan_lalu_token_lama_tidak_berlaku(
    klien: TestClient, sesi: Session
) -> None:
    pemilik(sesi)
    lama = masuk(klien)["token_segar"]
    baru = klien.post("/api/v1/auth/segarkan", json={"token_segar": lama})
    assert baru.status_code == 200
    assert baru.json()["token_segar"] != lama
    assert (
        klien.post("/api/v1/auth/segarkan", json={"token_segar": lama}).status_code == 401
    )


def test_keluar_lalu_tidak_bisa_disegarkan(klien: TestClient, sesi: Session) -> None:
    pemilik(sesi)
    segar = masuk(klien)["token_segar"]
    assert (
        klien.post("/api/v1/auth/keluar", json={"token_segar": segar}).status_code == 204
    )
    assert (
        klien.post("/api/v1/auth/segarkan", json={"token_segar": segar}).status_code
        == 401
    )


def test_ubah_sandi_sendiri(klien: TestClient, sesi: Session) -> None:
    pemilik(sesi)
    token = masuk(klien)["token_akses"]
    ubah = klien.post(
        "/api/v1/auth/ubah-sandi",
        json={"sandi_lama": SANDI, "sandi_baru": "sandibaru456"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert ubah.status_code == 204
    assert (
        klien.post(
            "/api/v1/auth/masuk",
            json={"nama_pengguna": "irvan", "sandi": "sandibaru456"},
        ).status_code
        == 200
    )


def test_alur_pemilik_membuat_akun_kasir(klien: TestClient, sesi: Session) -> None:
    """Alur yang menjadi syarat selesainya M0."""
    pemilik(sesi)
    token = masuk(klien)["token_akses"]
    h = {"Authorization": f"Bearer {token}"}

    buat = klien.post(
        "/api/v1/pengguna",
        json={
            "nama_pengguna": "kasir1",
            "nama_lengkap": "Kasir Satu",
            "sandi": "sandikasir1",
            "peran": "kasir",
        },
        headers=h,
    )
    assert buat.status_code == 201

    kasir_token = klien.post(
        "/api/v1/auth/masuk",
        json={"nama_pengguna": "kasir1", "sandi": "sandikasir1"},
    ).json()["token_akses"]
    ditolak = klien.get(
        "/api/v1/pengguna", headers={"Authorization": f"Bearer {kasir_token}"}
    )
    assert ditolak.status_code == 403
