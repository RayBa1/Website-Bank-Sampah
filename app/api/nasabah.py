from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Nasabah
from app.schemas.nasabah import NasabahRegister, RegistrationSuccess, NasabahResponse
from app.utils.security import get_current_nasabah, delete_session, extract_session_id
from app.utils.otp_service import OTPService

router = APIRouter(prefix="/nasabah", tags=["Nasabah"])

# ========== REGISTRASI NASABAH ==========

@router.post("/register", response_model=RegistrationSuccess)
def register_nasabah(data: NasabahRegister, db: Session = Depends(get_db)):
    """
    Endpoint untuk registrasi nasabah baru.
    Nasabah hanya perlu input data diri, TANPA password.
    Login nanti menggunakan OTP via HP.
    """
    
    # ===== VALIDASI NIK =====
    existing_nik = db.query(Nasabah).filter(Nasabah.nik == data.nik).first()
    if existing_nik:
        raise HTTPException(
            status_code=400, 
            detail="NIK sudah terdaftar. Silakan gunakan NIK lain atau login."
        )
    
    # ===== VALIDASI NO HP =====
    existing_phone = db.query(Nasabah).filter(Nasabah.no_hp == data.no_hp).first()
    if existing_phone:
        raise HTTPException(
            status_code=400, 
            detail="Nomor HP sudah terdaftar. Silakan gunakan nomor HP lain atau login."
        )
    
    # ===== BUAT NASABAH BARU =====
    new_nasabah = Nasabah(
        nik=data.nik,
        nama_nasabah=data.nama_nasabah,
        no_hp=data.no_hp,
        no_rekening=data.no_rekening,
        nama_bank=data.nama_bank,
        nama_pemilik_rekening=data.nama_pemilik_rekening,
        alamat=data.alamat,
        is_active=True
    )
    
    db.add(new_nasabah)
    db.commit()
    db.refresh(new_nasabah)
    
    return RegistrationSuccess(
        message="Registrasi berhasil!",
        nik=new_nasabah.nik,
        nama_nasabah=new_nasabah.nama_nasabah,
        no_hp=new_nasabah.no_hp
    )


# ========== GET PROFILE (Protected) ==========

@router.get("/profile", response_model=NasabahResponse)
def get_profile(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get profile nasabah yang sudah login.
    Butuh Authorization header dengan JWT token.
    
    Header format: Authorization: Bearer <token>
    """
    nik = get_current_nasabah(authorization)
    
    nasabah = db.query(Nasabah).filter(Nasabah.nik == nik).first()
    if not nasabah:
        raise HTTPException(status_code=404, detail="Nasabah tidak ditemukan")
    
    return nasabah

