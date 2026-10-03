# app/api/iot_ml.py  (FILE BARU)
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import ScanPending, StatusScan, JenisSampah
from app.schemas.iot_ml import IoTBeratCreate, MLDeteksiCreate, ScanResponse
from app.utils.security import verify_iot_api_key, verify_ml_api_key
from app.api.transaksi import buat_transaksi_iot, _save_base64_image

router = APIRouter(prefix="/iot-ml", tags=["IoT & ML (terpisah)"])

# Batas waktu menjodohkan berat (IoT) dengan deteksi (ML) dari mesin yang sama
WINDOW_DETIK = 15


def _kunci_mesin(db: Session, machine_id: str):
    """
    Kunci advisory per mesin selama transaksi DB berjalan.
    Mencegah race: IoT & ML masuk bersamaan lalu dua-duanya membuat baris baru
    (hasilnya dua baris setengah-jadi yang tidak pernah ketemu).
    Lepas otomatis saat commit/rollback.
    """
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:m))"), {"m": machine_id})


def _expire_lama(db: Session, machine_id: str):
    batas = datetime.utcnow() - timedelta(seconds=WINDOW_DETIK)
    db.query(ScanPending).filter(
        ScanPending.machine_id == machine_id,
        ScanPending.status == StatusScan.menunggu,
        ScanPending.created_at < batas,
    ).update({"status": StatusScan.kadaluarsa}, synchronize_session=False)


def _cari_scan(db: Session, machine_id: str, scan_id: Optional[str], kolom_kosong):
    """Cari baris 'menunggu' dari mesin ini yang sisi tujuannya (kolom_kosong) masih kosong."""
    q = db.query(ScanPending).filter(
        ScanPending.machine_id == machine_id,
        ScanPending.status == StatusScan.menunggu,
        kolom_kosong.is_(None),
    )
    if scan_id:
        q = q.filter(ScanPending.scan_id == scan_id)
    return q.order_by(ScanPending.created_at.asc()).first()


def _coba_selesaikan(db: Session, scan: ScanPending) -> ScanResponse:
    """Kalau berat DAN jenis sudah ada -> buat Transaksi lewat helper yang sama dengan /create-iot."""
    if scan.berat is None or scan.jenis_terdeteksi is None:
        sisi = "ML (jenis sampah)" if scan.jenis_terdeteksi is None else "IoT (berat)"
        return ScanResponse(id=scan.id, machine_id=scan.machine_id, status=scan.status.value,
                            pesan=f"Data diterima, menunggu data dari {sisi}")

    if not scan.nik:
        scan.status = StatusScan.butuh_review
        return ScanResponse(id=scan.id, machine_id=scan.machine_id, status=scan.status.value,
                            pesan="Data lengkap tapi NIK belum ada, butuh review admin")

    jenis = db.query(JenisSampah).filter(JenisSampah.kode_ml == scan.jenis_terdeteksi).first()
    if not jenis:
        scan.status = StatusScan.butuh_review
        return ScanResponse(id=scan.id, machine_id=scan.machine_id, status=scan.status.value,
                            pesan=f"Label '{scan.jenis_terdeteksi}' belum dipetakan ke jenis sampah, butuh review admin")

    hasil = buat_transaksi_iot(
        db,
        nik=scan.nik,
        items=[{
            "id_jenis": jenis.id_jenis,
            "berat": scan.berat,
            "jenis_terdeteksi": scan.jenis_terdeteksi,
            "confidence": scan.confidence,
            "foto_url": scan.foto_url,
        }],
        keterangan=f"Transaksi otomatis dari mesin {scan.machine_id} (IoT+ML)",
    )
    scan.status = StatusScan.selesai
    scan.id_transaksi = hasil.id_transaksi
    return ScanResponse(id=scan.id, machine_id=scan.machine_id, status=scan.status.value,
                        pesan="Data lengkap, transaksi berhasil dibuat", id_transaksi=hasil.id_transaksi)


# ========== TIM IoT: KIRIM BERAT ==========
@router.post("/berat", response_model=ScanResponse)
def kirim_berat(
    data: IoTBeratCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_iot_api_key),
):
    # DEBUG testing: tampilkan data IoT yang masuk ke terminal backend (hanya di development)
    if os.getenv("ENVIRONMENT", "development") == "development":
        print(f"\n{'='*60}")
        print(f"[IoT /berat] {datetime.now():%H:%M:%S} machine_id={data.machine_id} "
              f"berat={data.berat} nik={data.nik} scan_id={data.scan_id}")
        print(f"{'='*60}\n", flush=True)

    _kunci_mesin(db, data.machine_id)
    _expire_lama(db, data.machine_id)

    scan = _cari_scan(db, data.machine_id, data.scan_id, ScanPending.berat)
    if scan:
        scan.berat = data.berat
        scan.nik = scan.nik or data.nik
    else:
        scan = ScanPending(machine_id=data.machine_id, scan_id=data.scan_id,
                           nik=data.nik, berat=data.berat)
        db.add(scan)
        db.flush()

    hasil = _coba_selesaikan(db, scan)
    db.commit()
    return hasil


# ========== TIM ML: KIRIM HASIL DETEKSI ==========
@router.post("/deteksi", response_model=ScanResponse)
def kirim_deteksi(
    data: MLDeteksiCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_ml_api_key),
):
    _kunci_mesin(db, data.machine_id)
    _expire_lama(db, data.machine_id)

    foto_url = _save_base64_image(data.foto_base64)

    scan = _cari_scan(db, data.machine_id, data.scan_id, ScanPending.jenis_terdeteksi)
    if scan:
        scan.jenis_terdeteksi = data.jenis_terdeteksi
        scan.confidence = data.confidence
        scan.foto_url = foto_url
        scan.nik = scan.nik or data.nik
    else:
        scan = ScanPending(machine_id=data.machine_id, scan_id=data.scan_id, nik=data.nik,
                           jenis_terdeteksi=data.jenis_terdeteksi,
                           confidence=data.confidence, foto_url=foto_url)
        db.add(scan)
        db.flush()

    hasil = _coba_selesaikan(db, scan)
    db.commit()
    return hasil
