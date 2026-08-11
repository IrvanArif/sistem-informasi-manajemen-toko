import time

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.keamanan.sandi import hash_sandi
from app.kesalahan import KredensialSalah, TerlaluBanyakPercobaan
from app.layanan.otentikasi import BATAS_PERCOBAAN, keluar, masuk, segarkan
from app.model.pengguna import Pengguna, Peran
from app.model.token import TokenSegar

IP = "127.0.0.1"
SANDI = "rahasia123"


@pytest.fixture
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


def test_masuk_dengan_sandi_benar(sesi: Session, pemilik: Pengguna) -> None:
    pasangan = masuk(sesi, "irvan", SANDI, IP)
    assert pasangan.token_akses
    assert pasangan.token_segar


def test_masuk_dengan_sandi_salah_ditolak(sesi: Session, pemilik: Pengguna) -> None:
    with pytest.raises(KredensialSalah):
        masuk(sesi, "irvan", "salah", IP)


def test_nama_pengguna_tak_dikenal_ditolak(sesi: Session, pemilik: Pengguna) -> None:
    with pytest.raises(KredensialSalah):
        masuk(sesi, "tidak-ada", SANDI, IP)


def test_akun_nonaktif_tidak_bisa_masuk(sesi: Session, pemilik: Pengguna) -> None:
    pemilik.aktif = False
    sesi.commit()
    with pytest.raises(KredensialSalah):
        masuk(sesi, "irvan", SANDI, IP)


def test_pesan_sama_untuk_nama_salah_dan_sandi_salah(
    sesi: Session, pemilik: Pengguna
) -> None:
    """Pesan tak boleh membocorkan nama pengguna mana yang terdaftar."""
    with pytest.raises(KredensialSalah) as a:
        masuk(sesi, "tidak-ada", SANDI, IP)
    with pytest.raises(KredensialSalah) as b:
        masuk(sesi, "irvan", "salah", IP)
    assert a.value.pesan == b.value.pesan
    assert a.value.kode == b.value.kode


def test_waktu_jawaban_tidak_membocorkan_keberadaan_nama(
    sesi: Session, pemilik: Pengguna
) -> None:
    """Nama tak dikenal tetap melewati verifikasi umpan, sehingga waktunya
    tidak jauh lebih cepat daripada nama yang ada."""

    def ukur(nama: str) -> float:
        awal = time.perf_counter()
        with pytest.raises(KredensialSalah):
            masuk(sesi, nama, "salah", IP)
        return time.perf_counter() - awal

    ada = ukur("irvan")
    tak_ada = ukur("tidak-ada")
    assert tak_ada > ada * 0.4, (
        f"nama tak dikenal dijawab terlalu cepat ({tak_ada:.4f}s vs {ada:.4f}s), "
        "waktunya bisa dipakai menebak nama pengguna yang terdaftar"
    )


def test_percobaan_berlebih_diblokir(sesi: Session, pemilik: Pengguna) -> None:
    for _ in range(BATAS_PERCOBAAN):
        with pytest.raises(KredensialSalah):
            masuk(sesi, "irvan", "salah", IP)
    with pytest.raises(TerlaluBanyakPercobaan):
        masuk(sesi, "irvan", SANDI, IP)


def test_token_segar_berotasi(sesi: Session, pemilik: Pengguna) -> None:
    pertama = masuk(sesi, "irvan", SANDI, IP)
    kedua = segarkan(sesi, pertama.token_segar)
    assert kedua.token_segar != pertama.token_segar


def test_token_segar_lama_tidak_bisa_dipakai_ulang(
    sesi: Session, pemilik: Pengguna
) -> None:
    pertama = masuk(sesi, "irvan", SANDI, IP)
    segarkan(sesi, pertama.token_segar)
    with pytest.raises(KredensialSalah):
        segarkan(sesi, pertama.token_segar)


def test_pemakaian_ulang_mencabut_seluruh_sesi(sesi: Session, pemilik: Pengguna) -> None:
    """Token lama yang muncul lagi dianggap curian, seluruh sesi dicabut."""
    pertama = masuk(sesi, "irvan", SANDI, IP)
    kedua = segarkan(sesi, pertama.token_segar)
    with pytest.raises(KredensialSalah):
        segarkan(sesi, pertama.token_segar)
    with pytest.raises(KredensialSalah):
        segarkan(sesi, kedua.token_segar)


def test_keluar_mencabut_token(sesi: Session, pemilik: Pengguna) -> None:
    pasangan = masuk(sesi, "irvan", SANDI, IP)
    keluar(sesi, pasangan.token_segar)
    with pytest.raises(KredensialSalah):
        segarkan(sesi, pasangan.token_segar)


def test_token_segar_tersimpan_sebagai_hash_bukan_token(
    sesi: Session, pemilik: Pengguna
) -> None:
    pasangan = masuk(sesi, "irvan", SANDI, IP)
    tersimpan = sesi.execute(select(TokenSegar.token_hash)).scalars().all()
    assert pasangan.token_segar not in tersimpan
    assert all(len(h) == 64 for h in tersimpan)
