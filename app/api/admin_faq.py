from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import asc

from app.core.database import get_db
from app.models.models import FAQ
from app.schemas.faq import FAQCreate, FAQUpdate, FAQResponse
from app.utils.security import get_current_admin

router = APIRouter(prefix="/admin/faq", tags=["Admin - FAQ"])

@router.get("/", response_model=list[FAQResponse])
def list_faq_admin(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    get_current_admin(authorization)

    return db.query(FAQ).order_by(asc(FAQ.urutan)).all()


@router.post("/", response_model=FAQResponse)
def create_faq(
    data: FAQCreate,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    get_current_admin(authorization)

    faq = FAQ(**data.model_dump())
    db.add(faq)
    db.commit()
    db.refresh(faq)
    return faq


@router.patch("/{faq_id}", response_model=FAQResponse)
def update_faq(
    faq_id: int,
    data: FAQUpdate,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    get_current_admin(authorization)

    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ tidak ditemukan")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(faq, field, value)

    db.commit()
    db.refresh(faq)
    return faq


@router.delete("/{faq_id}")
def delete_faq(
    faq_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    get_current_admin(authorization)

    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ tidak ditemukan")

    db.delete(faq)
    db.commit()
    return {"message": "FAQ berhasil dihapus"}