import time

import pytest

from app.keamanan.token import (
    TokenTidakSah,
    baca_token_akses,
    buat_token_segar,
    hash_token_segar,
    terbitkan_token_akses,
)
from app.konfigurasi import ambil_pengaturan


def test_token_bisa_dibaca_kembali() -> None:
    isi = baca_token_akses(terbitkan_token_akses(7, "pemilik"))
    assert isi.pengguna_id == 7
    assert isi.peran == "pemilik"


def test_token_asing_ditolak() -> None:
    with pytest.raises(TokenTidakSah):
        baca_token_akses("bukan.token.sah")


def test_token_yang_diubah_ditolak() -> None:
    """Mengubah satu huruf pun merusak tanda tangannya."""
    token = terbitkan_token_akses(7, "kasir")
    rusak = token[:-3] + ("aaa" if not token.endswith("aaa") else "bbb")
    with pytest.raises(TokenTidakSah):
        baca_token_akses(rusak)


def test_token_bertanda_tangan_kunci_lain_ditolak(monkeypatch: pytest.MonkeyPatch) -> None:
    """Token dari sistem lain, atau dari kunci yang sudah diganti, ditolak."""
    token = terbitkan_token_akses(7, "pemilik")
    ambil_pengaturan.cache_clear()
    monkeypatch.setenv("RAHASIA_JWT", "kunci_yang_sama_sekali_berbeda_0123456789")
    try:
        with pytest.raises(TokenTidakSah):
            baca_token_akses(token)
    finally:
        ambil_pengaturan.cache_clear()


def test_token_kedaluwarsa_ditolak(monkeypatch: pytest.MonkeyPatch) -> None:
    ambil_pengaturan.cache_clear()
    monkeypatch.setenv("UMUR_TOKEN_AKSES_MENIT", "0")
    try:
        token = terbitkan_token_akses(7, "kasir")
        time.sleep(1.1)
        with pytest.raises(TokenTidakSah):
            baca_token_akses(token)
    finally:
        ambil_pengaturan.cache_clear()


def test_token_segar_disimpan_sebagai_hash() -> None:
    mentah, ter_hash = buat_token_segar()
    assert mentah != ter_hash
    assert hash_token_segar(mentah) == ter_hash
    assert len(ter_hash) == 64


def test_token_segar_selalu_berbeda() -> None:
    assert buat_token_segar()[0] != buat_token_segar()[0]
