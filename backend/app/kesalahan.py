from typing import Any


class KesalahanDomain(Exception):
    """Kegagalan yang diperkirakan, punya kode dan pesan berbahasa Indonesia.

    Dibedakan dari error sesungguhnya (bab 09): yang di sini adalah
    kejadian normal di toko, seperti sandi salah atau stok minus, dan
    layak mendapat cabang alur yang dirancang. Error sesungguhnya adalah
    hal yang seharusnya mustahil, dan itu dibiarkan naik menjadi 500.
    """

    def __init__(
        self,
        kode: str,
        pesan: str,
        status: int = 422,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(pesan)
        self.kode = kode
        self.pesan = pesan
        self.status = status
        self.detail = detail or {}

    def sebagai_jawaban(self) -> dict[str, Any]:
        return {"kode": self.kode, "pesan": self.pesan, "detail": self.detail}


class KredensialSalah(KesalahanDomain):
    def __init__(self) -> None:
        super().__init__(
            "KREDENSIAL_SALAH", "Nama pengguna atau sandi keliru", status=401
        )


class TidakBerhak(KesalahanDomain):
    def __init__(self) -> None:
        super().__init__(
            "TIDAK_BERHAK", "Peran Anda tidak mengizinkan tindakan ini", status=403
        )


class SesiHabis(KesalahanDomain):
    def __init__(self) -> None:
        super().__init__(
            "SESI_HABIS", "Sesi Anda telah berakhir. Silakan masuk lagi.", status=401
        )


class BelumMasuk(KesalahanDomain):
    def __init__(self) -> None:
        super().__init__(
            "BELUM_MASUK", "Silakan masuk terlebih dahulu", status=401
        )


class PemilikTerakhir(KesalahanDomain):
    def __init__(self) -> None:
        super().__init__(
            "PEMILIK_TERAKHIR",
            "Tindakan ini menyisakan nol akun pemilik aktif. "
            "Tunjuk pemilik lain lebih dulu.",
        )


class PeranSendiri(KesalahanDomain):
    def __init__(self) -> None:
        super().__init__(
            "PERAN_SENDIRI", "Anda tidak bisa mengubah peran akun Anda sendiri"
        )


class TerlaluBanyakPercobaan(KesalahanDomain):
    def __init__(self, menit: int) -> None:
        super().__init__(
            "TERLALU_BANYAK_PERCOBAAN",
            f"Terlalu banyak percobaan masuk. Coba lagi dalam {menit} menit.",
            status=429,
        )
