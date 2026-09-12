from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FAQBase(BaseModel):
    pertanyaan: str
    jawaban: str
    kategori: Optional[str] = None
    urutan: int = 0

class FAQCreate(FAQBase):
    pass

class FAQUpdate(BaseModel):
    pertanyaan: Optional[str] = None
    jawaban: Optional[str] = None
    kategori: Optional[str] = None
    urutan: Optional[int] = None
    is_active: Optional[bool] = None

class FAQResponse(FAQBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True