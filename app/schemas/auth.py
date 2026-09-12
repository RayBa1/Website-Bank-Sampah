from pydantic import BaseModel, Field
from typing import Optional

# ========== REQUEST SCHEMAS ==========

class RequestOTP(BaseModel):
    """Request untuk minta OTP"""
    no_hp: str = Field(..., pattern=r"^(\+62|0)[0-9]{9,12}$", description="Nomor HP")

class VerifyOTP(BaseModel):
    """Request untuk verify OTP dan login"""
    no_hp: str = Field(..., pattern=r"^(\+62|0)[0-9]{9,12}$")
    kode_otp: str = Field(..., min_length=6, max_length=6, description="6 digit OTP")

# ========== RESPONSE SCHEMAS ==========

class OTPResponse(BaseModel):
    """Response setelah request OTP"""
    message: str
    no_hp: str
    description: str = "OTP sudah dikirim via SMS"

class LoginResponse(BaseModel):
    """Response setelah login berhasil"""
    session_token: str
    token_type: str = "bearer"
    nik: str
    nama_nasabah: str
    message: str = "Login berhasil"

class NikLogin(BaseModel):
    """Login nasabah pakai NIK saja - TIDAK ADA OTP/PASSWORD (permintaan client)"""
    nik: str = Field(..., min_length=16, max_length=16, description="NIK 16 digit")