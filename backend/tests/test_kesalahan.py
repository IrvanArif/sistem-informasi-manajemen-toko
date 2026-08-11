import inspect
from typing import Any, cast

import pytest

from app import kesalahan as k


def semua_kesalahan() -> list[type[k.KesalahanDomain]]:
    return [
        obj
        for _, obj in inspect.getmembers(k, inspect.isclass)
        if issubclass(obj, k.KesalahanDomain) and obj is not k.KesalahanDomain
    ]


def test_bentuk_jawaban_seragam() -> None:
    jawaban = k.KredensialSalah().sebagai_jawaban()
    assert set(jawaban) == {"kode", "pesan", "detail"}
    assert jawaban["kode"] == "KREDENSIAL_SALAH"


@pytest.mark.parametrize("kelas", semua_kesalahan())
def test_setiap_kesalahan_punya_kode_dan_pesan(kelas: type[k.KesalahanDomain]) -> None:
    """Tak ada kesalahan yang lolos tanpa kode mesin atau pesan manusia."""
    # Pemanggilan sengaja dinamis supaya kesalahan baru yang ditambahkan
    # kelak ikut terperiksa tanpa perlu menyunting berkas uji ini.
    sig = inspect.signature(kelas.__init__)
    arg = [1] if len(sig.parameters) > 1 else []
    e: k.KesalahanDomain = cast(Any, kelas)(*arg)
    assert e.kode.isupper(), f"{kelas.__name__}: kode harus huruf besar"
    assert len(e.pesan) > 10, f"{kelas.__name__}: pesan terlalu pendek"
    assert 400 <= e.status < 500


def test_pesan_menuntun_bukan_sekadar_menolak() -> None:
    """Pesan menyebut langkah berikutnya, bukan cuma menyatakan gagal."""
    assert "lebih dulu" in k.PemilikTerakhir().pesan.lower()
    assert "masuk lagi" in k.SesiHabis().pesan.lower()
    assert "coba lagi" in k.TerlaluBanyakPercobaan(15).pesan.lower()


def test_detail_bisa_membawa_konteks() -> None:
    e = k.KesalahanDomain("X", "pesan panjang", detail={"produk_id": 7})
    assert e.sebagai_jawaban()["detail"] == {"produk_id": 7}
