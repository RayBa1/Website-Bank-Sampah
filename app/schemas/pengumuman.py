from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class StatusPengumumanEnum(str, Enum):
    draft = "draft"
    terbit = "terbit"
    arsip = "arsip"

# ========== REQUEST SCHEMAS ==========
class PengumumanCreate(BaseModel):
    judul: str = Field(..., min_length=3, max_length=200)
    isi: str = Field(..., min_length=1)
    gambar: Optional[str] = None
    status: StatusPengumumanEnum = StatusPengumumanEnum.draft

class PengumumanUpdate(BaseModel):
    """Semua field optional - cuma yang dikirim yang bakal di-update (partial update)"""
    judul: Optional[str] = Field(None, min_length=3, max_length=200)
    isi: Optional[str] = None
    gambar: Optional[str] = None
    status: Optional[StatusPengumumanEnum] = None

# ========== RESPONSE SCHEMAS ==========
class PengumumanResponse(BaseModel):
    id_pengumuman: int
    id_admin: int
    judul: str
    isi: str
    gambar: Optional[str]
    tanggal_publikasi: datetime
    status: StatusPengumumanEnum

    class Config:
        from_attributes = True