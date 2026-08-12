from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.kesalahan import KesalahanDomain
from app.model.kas import SesiKas, StatusSesi
from app.model.penjualan import MetodeBayar, Penjualan


def sesi_aktif(sesi: Session, kasir_id: int) -> SesiKas | None:
    return sesi.execute(
        select(SesiKas).where(
            SesiKas.kasir_id == kasir_id, SesiKas.status == StatusSesi.terbuka
        )
    ).scalar_one_or_none()


def buka_sesi(sesi: Session, kasir_id: int, modal_awal: int) -> SesiKas:
    if sesi_aktif(sesi, kasir_id) is not None:
        raise KesalahanDomain(
            "SESI_KAS_SUDAH_TERBUKA",
            "Sesi kas Anda masih terbuka. Tutup dulu sebelum membuka yang baru.",
        )
    if modal_awal < 0:
        raise KesalahanDomain("MODAL_NEGATIF", "Modal awal tidak boleh negatif")

    kas = SesiKas(
        kasir_id=kasir_id, waktu_buka=datetime.now(UTC), modal_awal=modal_awal
    )
    sesi.add(kas)
    sesi.commit()
    return kas


def hitung_kas_sistem(sesi: Session, kas: SesiKas) -> int:
    """Modal awal ditambah seluruh penjualan tunai dalam sesi ini.

    Hanya tunai. Transfer dan QRIS tidak pernah masuk laci, sehingga
    menghitungnya sebagai kas akan membuat selisih muncul setiap hari
    tanpa ada yang salah.
    """
    tunai = int(
        sesi.execute(
            select(func.coalesce(func.sum(Penjualan.total), 0)).where(
                Penjualan.sesi_kas_id == kas.id,
                Penjualan.metode_bayar == MetodeBayar.tunai,
            )
        ).scalar_one()
    )
    return kas.modal_awal + tunai


def tutup_sesi(
    sesi: Session, kas_id: int, kas_fisik: int, catatan: str | None, kasir_id: int
) -> SesiKas:
    kas = sesi.get(SesiKas, kas_id)
    if kas is None:
        raise KesalahanDomain("SESI_KAS_TIDAK_DITEMUKAN", "Sesi kas tidak ditemukan", 404)
    if kas.kasir_id != kasir_id:
        raise KesalahanDomain(
            "BUKAN_SESI_ANDA", "Sesi kas ini milik kasir lain", status=403
        )
    if kas.status is StatusSesi.tertutup:
        raise KesalahanDomain("SESI_KAS_SUDAH_TERTUTUP", "Sesi kas ini sudah ditutup")

    sistem = hitung_kas_sistem(sesi, kas)
    selisih = kas_fisik - sistem

    # Selisih tanpa penjelasan akan berulang tanpa pernah ditelusuri.
    # Sistem tidak pernah membetulkan angkanya sendiri.
    if selisih != 0 and not (catatan or "").strip():
        raise KesalahanDomain(
            "SELISIH_KAS_BUTUH_CATATAN",
            f"Isi catatan untuk selisih Rp{abs(selisih):,}".replace(",", ".")
            + ". Selisih yang tidak dijelaskan akan terulang tanpa pernah dicari sebabnya.",
            detail={"selisih": selisih, "kas_sistem": sistem, "kas_fisik": kas_fisik},
        )

    kas.waktu_tutup = datetime.now(UTC)
    kas.kas_sistem = sistem
    kas.kas_fisik = kas_fisik
    kas.selisih = selisih
    kas.catatan = (catatan or "").strip() or None
    kas.status = StatusSesi.tertutup
    sesi.commit()
    return kas


def wajib_sesi_terbuka(sesi: Session, kasir_id: int) -> SesiKas:
    kas = sesi_aktif(sesi, kasir_id)
    if kas is None:
        raise KesalahanDomain(
            "SESI_KAS_BELUM_DIBUKA",
            "Buka sesi kas lebih dulu dengan mengisi modal awal laci.",
        )
    return kas
