from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.keamanan.sandi import hash_sandi, verifikasi_sandi
from app.kesalahan import KesalahanDomain, PemilikTerakhir, PeranSendiri
from app.model.pengguna import Pengguna, Peran
from app.skema.pengguna import BuatPengguna, UbahPengguna


def _jumlah_pemilik_aktif(sesi: Session, kecuali_id: int | None = None) -> int:
    kueri = (
        select(func.count())
        .select_from(Pengguna)
        .where(Pengguna.peran == Peran.pemilik, Pengguna.aktif.is_(True))
    )
    if kecuali_id is not None:
        kueri = kueri.where(Pengguna.id != kecuali_id)
    return int(sesi.execute(kueri).scalar_one())


def daftar_pengguna(sesi: Session) -> list[Pengguna]:
    return list(
        sesi.execute(select(Pengguna).order_by(Pengguna.nama_pengguna)).scalars()
    )


def buat_pengguna(sesi: Session, data: BuatPengguna) -> Pengguna:
    sudah_ada = sesi.execute(
        select(Pengguna).where(Pengguna.nama_pengguna == data.nama_pengguna)
    ).scalar_one_or_none()
    if sudah_ada is not None:
        raise KesalahanDomain(
            "NAMA_PENGGUNA_TERPAKAI",
            f"Nama pengguna {data.nama_pengguna} sudah dipakai. Pilih nama lain.",
            detail={"nama_pengguna": data.nama_pengguna},
        )

    pengguna = Pengguna(
        nama_pengguna=data.nama_pengguna,
        nama_lengkap=data.nama_lengkap,
        sandi_hash=hash_sandi(data.sandi),
        peran=data.peran,
    )
    sesi.add(pengguna)
    sesi.commit()
    return pengguna


def ubah_pengguna(
    sesi: Session, pengguna_id: int, data: UbahPengguna, oleh: Pengguna
) -> Pengguna:
    pengguna = sesi.get(Pengguna, pengguna_id)
    if pengguna is None:
        raise KesalahanDomain(
            "PENGGUNA_TIDAK_DITEMUKAN", "Akun tidak ditemukan", status=404
        )

    if data.peran is not None and pengguna.id == oleh.id and data.peran != pengguna.peran:
        raise PeranSendiri

    tetap_pemilik_aktif = (data.peran or pengguna.peran) is Peran.pemilik and (
        pengguna.aktif if data.aktif is None else data.aktif
    )
    if not tetap_pemilik_aktif and _jumlah_pemilik_aktif(sesi, kecuali_id=pengguna.id) == 0:
        raise PemilikTerakhir

    if data.nama_lengkap is not None:
        pengguna.nama_lengkap = data.nama_lengkap
    if data.peran is not None:
        pengguna.peran = data.peran
    if data.aktif is not None:
        pengguna.aktif = data.aktif

    sesi.commit()
    return pengguna


def atur_ulang_sandi(sesi: Session, pengguna_id: int, sandi_baru: str) -> None:
    pengguna = sesi.get(Pengguna, pengguna_id)
    if pengguna is None:
        raise KesalahanDomain(
            "PENGGUNA_TIDAK_DITEMUKAN", "Akun tidak ditemukan", status=404
        )
    pengguna.sandi_hash = hash_sandi(sandi_baru)
    sesi.commit()


def ubah_sandi_sendiri(
    sesi: Session, pengguna: Pengguna, sandi_lama: str, sandi_baru: str
) -> None:
    if not verifikasi_sandi(sandi_lama, pengguna.sandi_hash):
        raise KesalahanDomain(
            "SANDI_LAMA_SALAH", "Sandi lama yang Anda masukkan keliru", status=400
        )
    pengguna.sandi_hash = hash_sandi(sandi_baru)
    sesi.commit()
