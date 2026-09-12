"""
Script untuk reset database - jalankan: python reset_db.py
"""
from app.core.database import engine, Base
from app.models.models import *

def reset_database():
    print("Menghapus semua table...")
    Base.metadata.drop_all(bind=engine)
    
    print("Membuat table baru...")
    Base.metadata.create_all(bind=engine)
    
    print("Database berhasil di-reset!")

if __name__ == "__main__":
    reset_database()