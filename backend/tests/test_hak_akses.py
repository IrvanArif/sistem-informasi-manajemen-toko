from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.keamanan.sandi import hash_sandi
from app.keamanan.token import terbitkan_token_akses
from app.model.pengguna import Pengguna, Peran

SANDI = "rahasia123"


def buat(sesi: Session, nama: str, peran: Peran) -> Pengguna:
    p = Pengguna(
        nama_pengguna=nama,
        nama_lengkap=nama.title(),
        sandi_hash=hash_sandi(SANDI),
        peran=peran,
    )
    sesi.add(p)
    sesi.commit()
    return p


def kepala(pengguna: Pengguna, peran: str | None = None) -> dict[str, str]:
    token = terbitkan_token_akses(pengguna.id, peran or pengguna.peran.value)
    return {"Authorization": f"Bearer {token}"}


def test_tanpa_token_ditolak(klien: TestClient) -> None:
    jawaban = klien.get("/api/v1/pengguna")
    assert jawaban.status_code == 401
    assert jawaban.json()["kode"] == "BELUM_MASUK"


def test_token_asing_ditolak(klien: TestClient) -> None:
    jawaban = klien.get(
        "/api/v1/pengguna", headers={"Authorization": "Bearer bukan.token.sah"}
    )
    assert jawaban.status_code == 401
    assert jawaban.json()["kode"] == "SESI_HABIS"


def test_kasir_ditolak_di_endpoint_pemilik(klien: TestClient, sesi: Session) -> None:
    kasir = buat(sesi, "kasir1", Peran.kasir)
    jawaban = klien.get("/api/v1/pengguna", headers=kepala(kasir))
    assert jawaban.status_code == 403
    assert jawaban.json()["kode"] == "TIDAK_BERHAK"


def test_peran_dibaca_dari_basis_data_bukan_dari_token(
    klien: TestClient, sesi: Session
) -> None:
    """Token dengan peran dipalsukan tetap ditolak."""
    kasir = buat(sesi, "kasir2", Peran.kasir)
    jawaban = klien.get("/api/v1/pengguna", headers=kepala(kasir, peran="pemilik"))
    assert jawaban.status_code == 403


def test_akun_nonaktif_langsung_kehilangan_akses(
    klien: TestClient, sesi: Session
) -> None:
    """Menonaktifkan akun berlaku seketika, tanpa menunggu token kedaluwarsa."""
    pemilik = buat(sesi, "irvan", Peran.pemilik)
    h = kepala(pemilik)
    assert klien.get("/api/v1/pengguna", headers=h).status_code == 200
    pemilik.aktif = False
    sesi.commit()
    assert klien.get("/api/v1/pengguna", headers=h).status_code == 401


def test_pemilik_boleh(klien: TestClient, sesi: Session) -> None:
    pemilik = buat(sesi, "irvan", Peran.pemilik)
    assert klien.get("/api/v1/pengguna", headers=kepala(pemilik)).status_code == 200


def test_jawaban_pengguna_tidak_pernah_memuat_sandi(
    klien: TestClient, sesi: Session
) -> None:
    pemilik = buat(sesi, "irvan", Peran.pemilik)
    isi = klien.get("/api/v1/pengguna", headers=kepala(pemilik)).json()
    assert isi
    for baris in isi:
        assert "sandi_hash" not in baris
        assert "sandi" not in baris
