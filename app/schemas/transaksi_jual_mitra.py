from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from decimal import Decimal


# ========== REQUEST ==========

class DetailJualMitraCreate(BaseModel):
    id_jenis: int = Field(..., gt=0)
    berat: Decimal = Field(..., gt=0, decimal_places=2)


class TransaksiJualMitraCreate(BaseModel):
    id_mitra: int = Field(..., gt=0)
    detail: List[DetailJualMitraCreate] = Field(..., min_length=1)
    keterangan: Optional[str] = None


# ========== RESPONSE ==========

class DetailJualMitraResponse(BaseModel):
    id_detail_jual: int
    id_jenis: int
    nama_jenis: Optional[str] = None
    berat: Decimal
    harga_per_kg: Decimal
    subtotal: Decimal

    class Config:
        from_attributes = True


class TransaksiJualMitraResponse(BaseModel):
    id_transaksi_jual: int
    id_mitra: int
    nama_mitra: Optional[str] = None
    id_admin: int
    tanggal_transaksi: datetime
    total_berat: Decimal
    total_nilai: Decimal
    keterangan: Optional[str]
    details: List[DetailJualMitraResponse]

    class Config:
        from_attributes = True