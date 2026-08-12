from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.basisdata import ambil_sesi

rute = APIRouter(tags=["sehat"])

akar = APIRouter(tags=["akar"])


@akar.get("/")
def akar_penjelas() -> dict[str, str]:
    """Menjelaskan diri saat alamat ini dibuka di browser.

    Alamat ini melayani API, bukan halaman. Tanpa jawaban ini, membukanya
    di browser hanya memberi 404 kosong yang tidak memberi tahu apa pun,
    padahal itu hal pertama yang dilakukan orang saat mencoba sistemnya.
    """
    return {
        "nama": "Sistem Informasi Manajemen Toko",
        "keterangan": "Alamat ini melayani API, bukan tampilan.",
        "tampilan": "Buka http://localhost:5173 untuk antarmukanya.",
        "kesehatan": "/api/v1/sehat",
    }


@rute.get("/sehat")
def sehat(sesi: Session = Depends(ambil_sesi)) -> dict[str, str]:
    """Menyentuh basis data, bukan sekadar menjawab.

    Endpoint kesehatan yang tidak menyentuh basis data akan menjawab
    "sehat" meski basis datanya mati, dan itu lebih berbahaya daripada
    tidak punya endpoint kesehatan sama sekali.
    """
    sesi.execute(text("SELECT 1"))
    return {"status": "sehat"}
