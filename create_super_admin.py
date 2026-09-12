"""
Script untuk membuat akun Super Admin pertama kali.
Jalankan manual: python create_super_admin.py
"""
import sys
from getpass import getpass
from app.core.database import SessionLocal, engine, Base
from app.models.models import Admin, RoleAdmin
from app.utils.security import hash_password

def create_super_admin():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("=== Setup Super Admin ===")
    nama_admin = input("Nama lengkap: ").strip()
    username = input("Username: ").strip()
    email = input("Email: ").strip()
    password = getpass("Password: ").strip()
    no_hp = input("No HP (opsional): ").strip() or None

    existing = db.query(Admin).filter(
        (Admin.username == username) | (Admin.email == email)
    ).first()
    if existing:
        print("❌ Username atau email sudah dipakai.")
        db.close()
        sys.exit(1)

    super_admin = Admin(
        nama_admin=nama_admin,
        username=username,
        email=email,
        password=hash_password(password),
        no_hp=no_hp,
        role=RoleAdmin.super_admin
    )
    db.add(super_admin)
    db.commit()
    print(f"Super admin '{username}' berhasil dibuat!")
    db.close()

if __name__ == "__main__":
    create_super_admin()