from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Nasabah, Admin, RoleAdmin
from app.schemas.auth import RequestOTP, VerifyOTP, OTPResponse, LoginResponse, NikLogin
from app.schemas.admin import SuperAdminLoginRequest, SuperAdminVerifyOTP, AdminLogin, AdminVerifyOTP
from app.utils.security import verify_password, create_session, delete_session, extract_session_id, check_login_rate_limit, reset_login_rate_limit
from app.utils.otp_service import OTPService

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ========== [NONAKTIF] NASABAH: REQUEST OTP ==========

# @router.post("/nasabah/request-otp", response_model=OTPResponse)
# def request_otp(data: RequestOTP, db: Session = Depends(get_db)):
#     """
#     Step 1: Nasabah minta OTP menggunakan nomor HP
#     OTP akan dikirim via SMS (untuk sekarang di-log ke console)
#     """
#     # Cek apakah nomor HP terdaftar
#     nasabah = db.query(Nasabah).filter(Nasabah.no_hp == data.no_hp).first()
    
#     if not nasabah:
#         raise HTTPException(
#             status_code=404, 
#             detail=" Nomor HP tidak terdaftar. Silakan daftar terlebih dahulu di /nasabah/register"
#         )
    
#     if not nasabah.is_active:
#         raise HTTPException(
#             status_code=403, 
#             detail=" Akun Anda telah dinonaktifkan. Hubungi admin."
#         )
    
#     # Generate OTP
#     kode_otp = OTPService.create_otp(db, data.no_hp)
    
#     #  DEVELOPMENT: Log OTP ke console (jangan di production!)
#     print(f"\n{'='*60}")
#     print(f" OTP untuk {data.no_hp}: {kode_otp}")
#     print(f"{'='*60}\n")
    
#     # Nanti diganti dengan send_sms():
#     # send_sms(data.no_hp, f"Kode OTP Bank Sampah: {kode_otp}. Berlaku 5 menit.")
    
#     return OTPResponse(
#         message=" OTP sudah dikirim",
#         no_hp=data.no_hp,
#         description=f"Periksa SMS di nomor {data.no_hp} (Berlaku 5 menit). Untuk development, cek console/terminal."
#     )


# ========== [NONAKTIF] NASABAH: VERIFY OTP & LOGIN ==========

# @router.post("/nasabah/verify-otp", response_model=LoginResponse)
# def verify_otp_login(data: VerifyOTP, db: Session = Depends(get_db)):
#     """
#     Step 2: Nasabah verify OTP untuk login
#     Akan return JWT token untuk akses endpoint protected
#     """
#     # Cek nomor HP
#     nasabah = db.query(Nasabah).filter(Nasabah.no_hp == data.no_hp).first()
#     if not nasabah:
#         raise HTTPException(
#             status_code=404, 
#             detail=" Nasabah tidak ditemukan"
#         )
    
#     if not nasabah.is_active:
#         raise HTTPException(
#             status_code=403, 
#             detail=" Akun Anda telah dinonaktifkan"
#         )
    
#     # Verify OTP
#     if not OTPService.verify_otp(db, data.no_hp, data.kode_otp):
#         raise HTTPException(
#             status_code=401, 
#             detail=" OTP salah atau sudah expired. Silakan minta OTP baru."
#         )
    
#     session_token = create_session(nasabah.nik)

#     return LoginResponse(
#         session_token=session_token,
#         nik=nasabah.nik,
#         nama_nasabah=nasabah.nama_nasabah,
#         message=" Login berhasil!"
#     )

@router.post("/nasabah/logout")
def logout_nasabah(authorization: str = Header(None)):
    """Logout nasabah - hapus session dari Redis"""
    session_id = extract_session_id(authorization)
    delete_session(session_id)
    return {"message": " Logout berhasil, sampai jumpa lagi!"}

# ========== ADMIN: LOGIN ==========

# ========== ADMIN: LOGIN STEP 1 (username + password → kirim OTP ke email) ==========
@router.post("/admin/login")
def login_admin(data: AdminLogin, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == data.username).first()

    if not admin or not verify_password(data.password, admin.password):
        raise HTTPException(status_code=401, detail="Username atau password salah")

    if not admin.email:
        raise HTTPException(status_code=400, detail="Akun ini belum punya email terdaftar, hubungi super admin")

    kode_otp = OTPService.create_otp(db, admin.email)

    print(f"\n{'='*60}")
    print(f" OTP Admin untuk {admin.email}: {kode_otp}")
    print(f"{'='*60}\n")

    return {
        "message": " Password benar, OTP sudah dikirim ke email",
        "email": admin.email,
        "description": f"Periksa email {admin.email} (Berlaku 5 menit). Untuk development, cek console."
    }

# ========== ADMIN: LOGIN STEP 2 (verify OTP → session) ==========
@router.post("/admin/verify-otp")
def verify_admin_otp(data: AdminVerifyOTP, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == data.username).first()

    if not admin:
        raise HTTPException(status_code=404, detail=" Admin tidak ditemukan")

    if not OTPService.verify_otp(db, admin.email, data.kode_otp):
        raise HTTPException(status_code=401, detail=" OTP salah atau sudah expired")

    session_token = create_session(admin.username, extra={"role": admin.role.value})

    return {
        "session_token": session_token,
        "token_type": "bearer",
        "role": admin.role.value,
        "message": " Login admin berhasil!"
    }

@router.post("/admin/logout")
def logout_admin(authorization: str = Header(None)):
    """Logout admin - hapus session dari Redis"""
    session_id = extract_session_id(authorization)
    delete_session(session_id)
    return {"message": " Logout admin berhasil"}

# ========== SUPER ADMIN: LOGIN STEP 1 (email + password → kirim OTP) ==========
@router.post("/super-admin/login")
def login_super_admin(data: SuperAdminLoginRequest, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(
        Admin.email == data.email,
        Admin.role == RoleAdmin.super_admin
    ).first()

    if not admin or not verify_password(data.password, admin.password):
        raise HTTPException(status_code=401, detail="Email atau password salah")

    kode_otp = OTPService.create_otp(db, admin.email)

    print(f"\n{'='*60}")
    print(f"OTP Super Admin untuk {admin.email}: {kode_otp}")
    print(f"{'='*60}\n")
    # Nanti diganti send_email(admin.email, ...)

    return {
        "message": "Password benar, OTP sudah dikirim ke email",
        "email": admin.email,
        "description": f"Periksa email {admin.email} (Berlaku 5 menit). Untuk development, cek console."
    }


# ========== SUPER ADMIN: LOGIN STEP 2 (verify OTP → session) ==========
@router.post("/super-admin/verify-otp")
def verify_super_admin_otp(data: SuperAdminVerifyOTP, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(
        Admin.email == data.email,
        Admin.role == RoleAdmin.super_admin
    ).first()

    if not admin:
        raise HTTPException(status_code=404, detail="Super admin tidak ditemukan")

    if not OTPService.verify_otp(db, admin.email, data.kode_otp):
        raise HTTPException(status_code=401, detail="OTP salah atau sudah expired")

    session_token = create_session(admin.username, extra={"role": admin.role.value})

    return {
        "session_token": session_token,
        "token_type": "bearer",
        "role": admin.role.value,
        "message": " Login super admin berhasil!"
    }


@router.post("/super-admin/logout")
def logout_super_admin(authorization: str = Header(None)):
    session_id = extract_session_id(authorization)
    delete_session(session_id)
    return {"message": " Logout super admin berhasil"}

# ========== NASABAH: LOGIN LANGSUNG PAKAI NIK (TANPA OTP/PASSWORD) ==========
@router.post("/nasabah/login", response_model=LoginResponse)
def login_nasabah_nik(data: NikLogin, db: Session = Depends(get_db)):
    """
    ⚠️ Login nasabah HANYA pakai NIK, tanpa password/OTP.
    Ini permintaan client - secara keamanan ini lebih lemah dari OTP,
    karena NIK bukan data rahasia. Rate limiting diterapkan untuk mitigasi.
    """
    check_login_rate_limit(data.nik)

    nasabah = db.query(Nasabah).filter(Nasabah.nik == data.nik).first()

    if not nasabah:
        raise HTTPException(status_code=404, detail=" NIK tidak terdaftar. Silakan daftar terlebih dahulu.")

    if not nasabah.is_active:
        raise HTTPException(status_code=403, detail=" Akun Anda telah dinonaktifkan. Hubungi admin.")

    reset_login_rate_limit(data.nik)  # login sukses, reset counter

    session_token = create_session(nasabah.nik)
    return LoginResponse(
        session_token=session_token,
        nik=nasabah.nik,
        nama_nasabah=nasabah.nama_nasabah,
        message=" Login berhasil!"
    )