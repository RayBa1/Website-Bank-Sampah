from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Admin, RoleAdmin
from app.schemas.admin import AdminRegister, AdminResponse
from app.utils.security import hash_password, require_super_admin, get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin Fitur"])

@router.get("/dashboard")
def get_admin_dashboard(authorization: str = Header(None)):
    get_current_admin(authorization)
    return {"message": "Ini halaman dashboard Admin"}

@router.get("/laporan")
def get_laporan(authorization: str = Header(None)):
    get_current_admin(authorization)
    return {"message": "Ini daftar laporan transaksi untuk Admin"}


# ========== SUPER ADMIN ONLY: BUAT AKUN ADMIN ==========
@router.post("/create-admin", response_model=AdminResponse)
def create_admin(
    data: AdminRegister,
    db: Session = Depends(get_db),
    _super_admin: dict = Depends(require_super_admin)
):
    existing = db.query(Admin).filter(
        (Admin.username == data.username) | (Admin.email == data.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username atau email sudah dipakai")

    new_admin = Admin(
        nama_admin=data.nama_admin,
        username=data.username,
        email=data.email,
        password=hash_password(data.password),
        no_hp=data.no_hp,
        role=RoleAdmin.admin
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return new_admin


# ========== SUPER ADMIN ONLY: HAPUS AKUN ADMIN ==========
@router.delete("/delete-admin/{id_admin}")
def delete_admin(
    id_admin: int,
    db: Session = Depends(get_db),
    _super_admin: dict = Depends(require_super_admin)
):
    admin = db.query(Admin).filter(Admin.id_admin == id_admin).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin tidak ditemukan")
    if admin.role == RoleAdmin.super_admin:
        raise HTTPException(status_code=403, detail="Tidak bisa menghapus akun super admin lewat endpoint ini")

    db.delete(admin)
    db.commit()
    return {"message": f"Admin '{admin.username}' berhasil dihapus"}
