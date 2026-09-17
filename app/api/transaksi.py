from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.models.models import (Transaksi, DetailTransaksi, 
                               JenisSampah, Nasabah, DataIoT)
from app.schemas.transaksi import (TransaksiCreate, TransaksiResponse, DetailTransaksiResponse, 
                                   TransaksiIoTCreate, TransaksiHistoryResponse)
from app.utils.security import get_current_admin, get_current_nasabah, verify_iot_api_key

router = APIRouter(prefix="/transaksi", tags=["Transaksi"])


# ========== ADMIN: BUAT TRANSAKSI SETORAN SAMPAH ==========
@router.post("/create", response_model=TransaksiResponse)
def create_transaksi(
    data: TransaksiCreate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Admin mencatat transaksi setoran sampah nasabah.
    Harga per kg diambil dari tabel jenis_sampah (bukan dari input admin),
    supaya harga tidak bisa dimanipulasi.
    Saldo nasabah otomatis bertambah sesuai total_nilai.
    """
    # Pastikan yang akses adalah admin (bukan nasabah)
    get_current_admin(authorization)

    # Validasi nasabah ada
    nasabah = db.query(Nasabah).filter(Nasabah.nik == data.nik).first()
    if not nasabah:
        raise HTTPException(status_code=404, detail="~~Nasabah dengan NIK tersebut tidak ditemukan")

    if not nasabah.is_active:
        raise HTTPException(status_code=403, detail="Akun nasabah ini sedang dinonaktifkan")

    total_berat = Decimal(0)
    total_nilai = Decimal(0)
    detail_list = []

    # Validasi jenis sampah & hitung total (harga_per_kg SELALU dari DB, bukan dari body)
    for item in data.detail:
        jenis = db.query(JenisSampah).filter(JenisSampah.id_jenis == item.id_jenis).first()
        if not jenis:
            raise HTTPException(status_code=404, detail=f"Jenis sampah id {item.id_jenis} tidak ditemukan")

        harga_per_kg = jenis.harga_per_kg
        subtotal = item.berat * harga_per_kg
        total_berat += item.berat
        total_nilai += subtotal

        detail_list.append({
            "id_jenis": item.id_jenis,
            "nama_jenis": jenis.nama_jenis,
            "berat": item.berat,
            "harga_per_kg": harga_per_kg,
            "subtotal": subtotal
        })

    # Buat transaksi
    transaksi = Transaksi(
        nik=data.nik,
        total_berat=total_berat,
        total_nilai=total_nilai,
        keterangan=data.keterangan
    )
    db.add(transaksi)
    db.flush()  # supaya dapat id_transaksi sebelum commit

    # Buat detail transaksi
    detail_responses = []
    for detail in detail_list:
        detail_transaksi = DetailTransaksi(
            id_transaksi=transaksi.id_transaksi,
            id_jenis=detail["id_jenis"],
            berat=detail["berat"],
            harga_per_kg=detail["harga_per_kg"],
            subtotal=detail["subtotal"]
        )
        db.add(detail_transaksi)
        db.flush()
        detail_responses.append(DetailTransaksiResponse(
            id_detail=detail_transaksi.id_detail,
            id_jenis=detail["id_jenis"],
            nama_jenis=detail["nama_jenis"],
            berat=detail["berat"],
            harga_per_kg=detail["harga_per_kg"],
            subtotal=detail["subtotal"]
        ))

    # TAMBAH SALDO NASABAH — hanya bisa terjadi lewat jalur ini (admin only)
    nasabah.saldo = nasabah.saldo + total_nilai

    db.commit()
    db.refresh(transaksi)
    db.refresh(nasabah)

    return TransaksiResponse(
        id_transaksi=transaksi.id_transaksi,
        nik=transaksi.nik,
        tanggal_transaksi=transaksi.tanggal_transaksi,
        total_berat=transaksi.total_berat,
        total_nilai=transaksi.total_nilai,
        keterangan=transaksi.keterangan,
        saldo_nasabah_sekarang=nasabah.saldo,
        details=detail_responses
    )

# ========== ADMIN: LIHAT SEMUA RIWAYAT TRANSAKSI (BARU) ==========
@router.get("/history-admin", response_model=list[TransaksiHistoryResponse])
def get_history_admin(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
    nik: Optional[str] = None,
    tanggal_mulai: Optional[date] = None,
    tanggal_akhir: Optional[date] = None,
    limit: int = 100,
):
    """Admin lihat semua riwayat transaksi, bisa difilter NIK & rentang tanggal."""
    get_current_admin(authorization)
    query = db.query(Transaksi)
    if nik:
        query = query.filter(Transaksi.nik == nik)
    if tanggal_mulai:
        query = query.filter(Transaksi.tanggal_transaksi >= tanggal_mulai)
    if tanggal_akhir:
        query = query.filter(Transaksi.tanggal_transaksi <= tanggal_akhir)
    return query.order_by(Transaksi.tanggal_transaksi.desc()).limit(limit).all()


# ========== NASABAH: LIHAT HISTORY TRANSAKSI SENDIRI ==========
@router.get("/history", response_model=list[TransaksiHistoryResponse])
def get_history(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Nasabah lihat riwayat transaksi sendiri (pakai token nasabah)"""
    nik = get_current_nasabah(authorization)
    return db.query(Transaksi)\
        .filter(Transaksi.nik == nik)\
        .order_by(Transaksi.tanggal_transaksi.desc())\
        .all()

# ========== IOT: BUAT TRANSAKSI OTOMATIS DARI DETEKSI ML ==========
@router.post("/create-iot", response_model=TransaksiResponse)
def create_transaksi_iot(
    data: TransaksiIoTCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_iot_api_key)
):
    """
    Endpoint khusus device IoT untuk mencatat transaksi otomatis.
    Auth pakai API Key (header X-API-Key), BUKAN session token admin.
    Setiap item juga dicatat ke tabel data_iot untuk jejak audit hasil ML.
    """
    nasabah = db.query(Nasabah).filter(Nasabah.nik == data.nik).first()
    if not nasabah:
        raise HTTPException(status_code=404, detail="Nasabah dengan NIK tersebut tidak ditemukan")

    if not nasabah.is_active:
        raise HTTPException(status_code=403, detail="Akun nasabah ini sedang dinonaktifkan")

    total_berat = Decimal(0)
    total_nilai = Decimal(0)
    detail_list = []

    for item in data.detail:
        jenis = db.query(JenisSampah).filter(JenisSampah.id_jenis == item.id_jenis).first()
        if not jenis:
            raise HTTPException(status_code=404, detail=f"Jenis sampah id {item.id_jenis} tidak ditemukan")

        harga_per_kg = jenis.harga_per_kg
        subtotal = item.berat * harga_per_kg
        total_berat += item.berat
        total_nilai += subtotal

        detail_list.append({
            "id_jenis": item.id_jenis,
            "nama_jenis": jenis.nama_jenis,
            "berat": item.berat,
            "harga_per_kg": harga_per_kg,
            "subtotal": subtotal,
            "jenis_terdeteksi": item.jenis_terdeteksi,
            "confidence": item.confidence
        })

    transaksi = Transaksi(
        nik=data.nik,
        total_berat=total_berat,
        total_nilai=total_nilai,
        keterangan=data.keterangan or "Transaksi otomatis dari IoT"
    )
    db.add(transaksi)
    db.flush()

    detail_responses = []
    for detail in detail_list:
        detail_transaksi = DetailTransaksi(
            id_transaksi=transaksi.id_transaksi,
            id_jenis=detail["id_jenis"],
            berat=detail["berat"],
            harga_per_kg=detail["harga_per_kg"],
            subtotal=detail["subtotal"]
        )
        db.add(detail_transaksi)

        # Catat jejak deteksi ML ke tabel data_iot
        data_iot = DataIoT(
            id_transaksi=transaksi.id_transaksi,
            jenis_terdeteksi=detail["jenis_terdeteksi"],
            berat_sensor=detail["berat"],
            confidence=detail["confidence"]
        )
        db.add(data_iot)
        db.flush()

        detail_responses.append(DetailTransaksiResponse(
            id_detail=detail_transaksi.id_detail,
            id_jenis=detail["id_jenis"],
            nama_jenis=detail["nama_jenis"],
            berat=detail["berat"],
            harga_per_kg=detail["harga_per_kg"],
            subtotal=detail["subtotal"]
        ))

    nasabah.saldo = nasabah.saldo + total_nilai

    db.commit()
    db.refresh(transaksi)
    db.refresh(nasabah)

    return TransaksiResponse(
        id_transaksi=transaksi.id_transaksi,
        nik=transaksi.nik,
        tanggal_transaksi=transaksi.tanggal_transaksi,
        total_berat=transaksi.total_berat,
        total_nilai=transaksi.total_nilai,
        keterangan=transaksi.keterangan,
        saldo_nasabah_sekarang=nasabah.saldo,
        details=detail_responses
    )