from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import asc

from app.core.database import get_db
from app.models.models import FAQ
from app.schemas.faq import FAQResponse

router = APIRouter(prefix="/faq", tags=["Nasabah - FAQ"])

@router.get("/", response_model=list[FAQResponse])
def list_faq_public(kategori: str | None = None, db: Session = Depends(get_db)):
    query = db.query(FAQ).filter(FAQ.is_active == True)
    if kategori:
        query = query.filter(FAQ.kategori == kategori)
    return query.order_by(asc(FAQ.urutan)).all()