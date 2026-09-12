from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal

# ========== REQUEST SCHEMAS ==========

class NasabahRegister(BaseModel):
    """Schema untuk registrasi nasabah baru (TANPA PASSWORD - pakai OTP)"""
    nik: str = Field(
        ..., 
        min_length=16, 
        max_length=16, 
        description="NIK 16 digit"
    )
    nama_nasabah: str = Field(
        ..., 
        min_length=3, 
        max_length=100,
        description="Nama lengkap"
    )
    no_hp: str = Field(
        ..., 
        pattern=r"^(\+62|0)[0-9]{9,12}$",
        description="Format: 081234567890 atau +6281234567890"
    )
    no_rekening: str = Field(
        ..., 
        min_length=10,
        description="Nomor rekening bank"
    )
    nama_bank: str = Field(
        ..., 
        min_length=3,
        description="Nama bank (BCA, BNI, Mandiri, dll)"
    )
    nama_pemilik_rekening: str = Field(
        ..., 
        min_length=3,
        description="Nama pemilik rekening (sesuai kartu identitas)"
    )
    alamat: Optional[str] = Field(
        None,
        description="Alamat lengkap (optional)"
    )


# ========== RESPONSE SCHEMAS ==========

class NasabahResponse(BaseModel):
    """Response data nasabah (TANPA PASSWORD)"""
    nik: str
    nama_nasabah: str
    no_hp: str
    no_rekening: str
    nama_bank: str
    nama_pemilik_rekening: str
    alamat: Optional[str]
    saldo: Decimal
    tanggal_daftar: datetime

    class Config:
        from_attributes = True


class RegistrationSuccess(BaseModel):
    """Response sukses registrasi"""
    message: str
    nik: str
    nama_nasabah: str
    no_hp: str
    next_step: str = "Silakan login menggunakan nomor HP"