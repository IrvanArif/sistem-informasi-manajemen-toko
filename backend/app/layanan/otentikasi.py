from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.keamanan.sandi import hash_sandi, verifikasi_sandi
from app.keamanan.token import buat_token_segar, hash_token_segar, terbitkan_token_akses
from app.kesalahan import KredensialSalah, TerlaluBanyakPercobaan
from app.konfigurasi import ambil_pengaturan
from app.model.pengguna import Pengguna
from app.model.percobaan_masuk import PercobaanMasuk
from app.model.token import TokenSegar

BATAS_PERCOBAAN = 5
JENDELA_MENIT = 15

# Hash tetap untuk dibandingkan saat nama pengguna tidak ditemukan. Tanpa
# ini, permintaan dengan nama tak dikenal dijawab jauh lebih cepat daripada
# yang namanya ada, dan selisih waktu itu cukup untuk menebak nama pengguna
# mana yang terdaftar.
_HASH_UMPAN = hash_sandi("umpan-agar-waktu-jawaban-seragam")


@dataclass(frozen=True)
class PasanganToken:
    token_akses: str
    token_segar: str


def _jumlah_gagal_terakhir(sesi: Session, nama_pengguna: str, alamat_ip: str) -> int:
    sejak = datetime.now(UTC) - timedelta(minutes=JENDELA_MENIT)
    kueri = (
        select(func.count())
        .select_from(PercobaanMasuk)
        .where(
            PercobaanMasuk.berhasil.is_(False),
            PercobaanMasuk.dibuat_pada >= sejak,
            (PercobaanMasuk.nama_pengguna == nama_pengguna)
            | (PercobaanMasuk.alamat_ip == alamat_ip),
        )
    )
    return int(sesi.execute(kueri).scalar_one())


def _terbitkan_pasangan(sesi: Session, pengguna: Pengguna) -> PasanganToken:
    mentah, ter_hash = buat_token_segar()
    sesi.add(
        TokenSegar(
            pengguna_id=pengguna.id,
            token_hash=ter_hash,
            kedaluwarsa_pada=datetime.now(UTC)
            + timedelta(days=ambil_pengaturan().umur_token_segar_hari),
        )
    )
    sesi.flush()
    return PasanganToken(
        token_akses=terbitkan_token_akses(pengguna.id, pengguna.peran.value),
        token_segar=mentah,
    )


def masuk(sesi: Session, nama_pengguna: str, sandi: str, alamat_ip: str) -> PasanganToken:
    if _jumlah_gagal_terakhir(sesi, nama_pengguna, alamat_ip) >= BATAS_PERCOBAAN:
        raise TerlaluBanyakPercobaan(JENDELA_MENIT)

    pengguna = sesi.execute(
        select(Pengguna).where(Pengguna.nama_pengguna == nama_pengguna)
    ).scalar_one_or_none()

    if pengguna is None:
        verifikasi_sandi(sandi, _HASH_UMPAN)  # samakan waktu jawaban
        sah = False
    else:
        sah = pengguna.aktif and verifikasi_sandi(sandi, pengguna.sandi_hash)

    sesi.add(
        PercobaanMasuk(nama_pengguna=nama_pengguna, alamat_ip=alamat_ip, berhasil=sah)
    )

    if not sah or pengguna is None:
        sesi.commit()
        raise KredensialSalah

    pasangan = _terbitkan_pasangan(sesi, pengguna)
    sesi.commit()
    return pasangan


def segarkan(sesi: Session, token_segar_mentah: str) -> PasanganToken:
    baris = sesi.execute(
        select(TokenSegar).where(TokenSegar.token_hash == hash_token_segar(token_segar_mentah))
    ).scalar_one_or_none()

    if baris is None or baris.kedaluwarsa_pada < datetime.now(UTC):
        raise KredensialSalah

    if baris.dicabut_pada is not None:
        # Token yang sudah dicabut dipakai lagi. Kemungkinan besar tokennya
        # dicuri: pemilik sah sudah menukarnya, lalu ada pihak lain memakai
        # salinan lama. Seluruh sesi pengguna itu dicabut, sehingga pencuri
        # maupun pemilik sah sama-sama harus masuk ulang.
        for lain in sesi.execute(
            select(TokenSegar).where(TokenSegar.pengguna_id == baris.pengguna_id)
        ).scalars():
            lain.dicabut_pada = datetime.now(UTC)
        sesi.commit()
        raise KredensialSalah

    baris.dicabut_pada = datetime.now(UTC)
    pengguna = sesi.get(Pengguna, baris.pengguna_id)
    if pengguna is None or not pengguna.aktif:
        sesi.commit()
        raise KredensialSalah

    pasangan = _terbitkan_pasangan(sesi, pengguna)
    sesi.commit()
    return pasangan


def keluar(sesi: Session, token_segar_mentah: str) -> None:
    baris = sesi.execute(
        select(TokenSegar).where(TokenSegar.token_hash == hash_token_segar(token_segar_mentah))
    ).scalar_one_or_none()
    if baris is not None and baris.dicabut_pada is None:
        baris.dicabut_pada = datetime.now(UTC)
    sesi.commit()
