import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# Mengambil URL Database dari file .env
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Membuat engine SQLAlchemy
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Membuat SessionLocal untuk transaksi database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class untuk membuat model/tabel
Base = declarative_base()

# Dependency untuk mendapatkan koneksi DB di endpoint
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()