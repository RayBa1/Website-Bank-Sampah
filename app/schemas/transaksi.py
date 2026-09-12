from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from decimal import Decimal


# ========== REQUEST SCHEMAS ==========

class DetailTransaksiCreate(BaseModel):
    """Admin cuma perlu kirim id_jenis + berat. Harga diambil dari DB (JenisSampah), bukan dari input,
    supaya harga tidak bisa dimanipulasi dari sisi client."""
    id_jenis: int = Field(..., gt=0, description="ID jenis sampah dari dropdown")
    berat: Decimal = Field(..., gt=0, decimal_places=2, description="Berat sampah dalam KG")


class TransaksiCreate(BaseModel):
    """Dipakai ADMIN untuk mencatat transaksi setoran sampah nasabah"""
    nik: str = Field(..., min_length=16, max_length=16, description="NIK nasabah yang menyetor sampah")
    detail: List[DetailTransaksiCreate] = Field(..., min_length=1)
    keterangan: Optional[str] = None


# ========== RESPONSE SCHEMAS ==========

class DetailTransaksiResponse(BaseModel):
    id_detail: int
    id_jenis: int
    nama_jenis: Optional[str] = None
    berat: Decimal
    harga_per_kg: Decimal
    subtotal: Decimal

    class Config:
        from_attributes = True


class TransaksiResponse(BaseModel):
    id_transaksi: int
    nik: str
    tanggal_transaksi: datetime
    total_berat: Decimal
    total_nilai: Decimal
    keterangan: Optional[str]
    saldo_nasabah_sekarang: Decimal
    details: List[DetailTransaksiResponse]

    class Config:
        from_attributes = True

# ========== SCHEMA KHUSUS IOT ==========

class DetailTransaksiIoT(BaseModel):
    """Detail sampah yang terdeteksi ML, termasuk confidence score"""
    id_jenis: int = Field(..., gt=0, description="ID jenis sampah hasil mapping dari deteksi ML")
    berat: Decimal = Field(..., gt=0, decimal_places=2, description="Berat dari sensor (KG)")
    jenis_terdeteksi: Optional[str] = Field(None, description="Label mentah hasil deteksi ML, misal 'plastic_bottle'")
    confidence: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2, description="Confidence level ML dalam persen (0-100)")


class TransaksiIoTCreate(BaseModel):
    """Dipakai oleh device IoT untuk mencatat transaksi otomatis dari hasil deteksi ML"""
    nik: str = Field(..., min_length=16, max_length=16, description="NIK nasabah yang menyetor sampah")
    detail: List[DetailTransaksiIoT] = Field(..., min_length=1)
    keterangan: Optional[str] = None