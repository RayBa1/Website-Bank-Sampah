from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, List
from decimal import Decimal


# ========== REQUEST: MITRA ==========

class MitraPengepulCreate(BaseModel):
    nama_mitra: str = Field(..., min_length=3, max_length=150)
    deskripsi: Optional[str] = None
    alamat: Optional[str] = None
    no_hp: Optional[str] = Field(None, pattern=r"^(\+62|0)[0-9]{9,12}$")
    email: Optional[EmailStr] = None
    nama_penanggung_jawab: Optional[str] = Field(None, max_length=100)


class MitraPengepulUpdate(BaseModel):
    """Partial update - semua field optional"""
    nama_mitra: Optional[str] = Field(None, min_length=3, max_length=150)
    deskripsi: Optional[str] = None
    alamat: Optional[str] = None
    no_hp: Optional[str] = Field(None, pattern=r"^(\+62|0)[0-9]{9,12}$")
    email: Optional[EmailStr] = None
    nama_penanggung_jawab: Optional[str] = Field(None, max_length=100)


class MitraStatusUpdate(BaseModel):
    is_active: bool


# ========== REQUEST: HARGA PER JENIS SAMPAH ==========

class HargaMitraCreate(BaseModel):
    id_jenis: int = Field(..., gt=0)
    harga_beli_per_kg: Decimal = Field(..., gt=0, decimal_places=2)


class HargaMitraUpdate(BaseModel):
    harga_beli_per_kg: Decimal = Field(..., gt=0, decimal_places=2)


# ========== RESPONSE ==========

class HargaMitraResponse(BaseModel):
    id_harga: int
    id_jenis: int
    nama_jenis: Optional[str] = None
    harga_beli_per_kg: Decimal
    tanggal_diperbarui: datetime

    class Config:
        from_attributes = True


class MitraPengepulResponse(BaseModel):
    id_mitra: int
    nama_mitra: str
    deskripsi: Optional[str]
    alamat: Optional[str]
    no_hp: Optional[str]
    email: Optional[str]
    nama_penanggung_jawab: Optional[str]
    is_active: bool
    tanggal_ditambahkan: datetime
    tanggal_diperbarui: datetime

    class Config:
        from_attributes = True


class MitraPengepulDetailResponse(MitraPengepulResponse):
    """Response detail, termasuk daftar harga per jenis sampah"""
    harga_jenis_sampah: List[HargaMitraResponse] = []


class MitraListResponse(BaseModel):
    total: int
    data: List[MitraPengepulResponse]