from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from decimal import Decimal

from app.core.database import get_db
from app.models.models import (
    TransaksiJualMitra, DetailTransaksiJualMitra,
    MitraPengepul, HargaMitraPengepul, JenisSampah, Admin
)
from app.schemas.transaksi_jual_mitra import (
    TransaksiJualMitraCreate, TransaksiJualMitraResponse, DetailJualMitraResponse
)
from app.utils.security import get_current_admin

router = APIRouter(prefix="/transaksi-jual-mitra", tags=["Transaksi Jual ke Mitra"])


# ========== ADMIN: BUAT TRANSAKSI JUAL KE MITRA ==========
@router.post("/create", response_model=TransaksiJualMitraResponse)
def create_transaksi_jual_mitra(
    data: TransaksiJualMitraCreate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Admin mencatat transaksi penjualan sampah ke mitra pengepul.
    Harga per kg diambil dari HargaMitraPengepul (harga khusus mitra ini),
    bukan dari input admin, supaya harga tidak bisa dimanipulasi.
    """
    admin_session = get_current_admin(authorization)
    admin = db.query(Admin).filter(Admin.username == admin_session["sub"]).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin tidak ditemukan")

    mitra = db.query(MitraPengepul).filter(MitraPengepul.id_mitra == data.id_mitra).first()
    if not mitra:
        raise HTTPException(status_code=404, detail="Mitra pengepul tidak ditemukan")

    if not mitra.is_active:
        raise HTTPException(status_code=403, detail="Kerjasama dengan mitra ini sedang tidak aktif")

    total_berat = Decimal(0)
    total_nilai = Decimal(0)
    detail_list = []

    for item in data.detail:
        jenis = db.query(JenisSampah).filter(JenisSampah.id_jenis == item.id_jenis).first()
        if not jenis:
            raise HTTPException(status_code=404, detail=f"Jenis sampah id {item.id_jenis} tidak ditemukan")

        # Harga WAJIB ada dulu di HargaMitraPengepul untuk jenis sampah ini
        harga_mitra = db.query(HargaMitraPengepul).filter(
            HargaMitraPengepul.id_mitra == data.id_mitra,
            HargaMitraPengepul.id_jenis == item.id_jenis
        ).first()
        if not harga_mitra:
            raise HTTPException(
                status_code=400,
                detail=f"Mitra ini belum punya harga untuk jenis sampah '{jenis.nama_jenis}'. "
                       f"Tambahkan harga dulu lewat /mitra-pengepul/{data.id_mitra}/harga"
            )

        harga_per_kg = harga_mitra.harga_beli_per_kg
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

    transaksi_jual = TransaksiJualMitra(
        id_mitra=data.id_mitra,
        id_admin=admin.id_admin,
        total_berat=total_berat,
        total_nilai=total_nilai,
        keterangan=data.keterangan
    )
    db.add(transaksi_jual)
    db.flush()

    detail_responses = []
    for detail in detail_list:
        detail_jual = DetailTransaksiJualMitra(
            id_transaksi_jual=transaksi_jual.id_transaksi_jual,
            id_jenis=detail["id_jenis"],
            berat=detail["berat"],
            harga_per_kg=detail["harga_per_kg"],
            subtotal=detail["subtotal"]
        )
        db.add(detail_jual)
        db.flush()
        detail_responses.append(DetailJualMitraResponse(
            id_detail_jual=detail_jual.id_detail_jual,
            id_jenis=detail["id_jenis"],
            nama_jenis=detail["nama_jenis"],
            berat=detail["berat"],
            harga_per_kg=detail["harga_per_kg"],
            subtotal=detail["subtotal"]
        ))

    db.commit()
    db.refresh(transaksi_jual)

    return TransaksiJualMitraResponse(
        id_transaksi_jual=transaksi_jual.id_transaksi_jual,
        id_mitra=transaksi_jual.id_mitra,
        nama_mitra=mitra.nama_mitra,
        id_admin=transaksi_jual.id_admin,
        tanggal_transaksi=transaksi_jual.tanggal_transaksi,
        total_berat=transaksi_jual.total_berat,
        total_nilai=transaksi_jual.total_nilai,
        keterangan=transaksi_jual.keterangan,
        details=detail_responses
    )


# ========== ADMIN: LIST SEMUA TRANSAKSI JUAL KE MITRA ==========
@router.get("/", response_model=list[TransaksiJualMitraResponse])
def list_transaksi_jual_mitra(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    get_current_admin(authorization)

    transaksi_list = db.query(TransaksiJualMitra)\
        .order_by(TransaksiJualMitra.tanggal_transaksi.desc())\
        .all()

    return [
        TransaksiJualMitraResponse(
            id_transaksi_jual=t.id_transaksi_jual,
            id_mitra=t.id_mitra,
            nama_mitra=t.mitra.nama_mitra if t.mitra else None,
            id_admin=t.id_admin,
            tanggal_transaksi=t.tanggal_transaksi,
            total_berat=t.total_berat,
            total_nilai=t.total_nilai,
            keterangan=t.keterangan,
            details=[
                DetailJualMitraResponse(
                    id_detail_jual=d.id_detail_jual,
                    id_jenis=d.id_jenis,
                    nama_jenis=d.jenis_sampah.nama_jenis if d.jenis_sampah else None,
                    berat=d.berat,
                    harga_per_kg=d.harga_per_kg,
                    subtotal=d.subtotal
                ) for d in t.details
            ]
        ) for t in transaksi_list
    ]


# ========== ADMIN: HISTORY TRANSAKSI KE 1 MITRA TERTENTU ==========
@router.get("/mitra/{id_mitra}", response_model=list[TransaksiJualMitraResponse])
def get_transaksi_by_mitra(
    id_mitra: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    get_current_admin(authorization)

    mitra = db.query(MitraPengepul).filter(MitraPengepul.id_mitra == id_mitra).first()
    if not mitra:
        raise HTTPException(status_code=404, detail="Mitra pengepul tidak ditemukan")

    transaksi_list = db.query(TransaksiJualMitra)\
        .filter(TransaksiJualMitra.id_mitra == id_mitra)\
        .order_by(TransaksiJualMitra.tanggal_transaksi.desc())\
        .all()

    return [
        TransaksiJualMitraResponse(
            id_transaksi_jual=t.id_transaksi_jual,
            id_mitra=t.id_mitra,
            nama_mitra=mitra.nama_mitra,
            id_admin=t.id_admin,
            tanggal_transaksi=t.tanggal_transaksi,
            total_berat=t.total_berat,
            total_nilai=t.total_nilai,
            keterangan=t.keterangan,
            details=[
                DetailJualMitraResponse(
                    id_detail_jual=d.id_detail_jual,
                    id_jenis=d.id_jenis,
                    nama_jenis=d.jenis_sampah.nama_jenis if d.jenis_sampah else None,
                    berat=d.berat,
                    harga_per_kg=d.harga_per_kg,
                    subtotal=d.subtotal
                ) for d in t.details
            ]
        ) for t in transaksi_list
    ]