from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.basisdata import ambil_sesi

rute = APIRouter(tags=["sehat"])


@rute.get("/sehat")
def sehat(sesi: Session = Depends(ambil_sesi)) -> dict[str, str]:
    """Menyentuh basis data, bukan sekadar menjawab.

    Endpoint kesehatan yang tidak menyentuh basis data akan menjawab
    "sehat" meski basis datanya mati, dan itu lebih berbahaya daripada
    tidak punya endpoint kesehatan sama sekali.
    """
    sesi.execute(text("SELECT 1"))
    return {"status": "sehat"}
