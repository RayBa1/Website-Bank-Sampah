from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal


# ========== RESPONSE: FULL DATA NASABAH (untuk admin) ==========

class NasabahAdminResponse(BaseModel):
    """Semua field nasabah, termasuk saldo & is_active — khusus dilihat admin"""
    nik: str
    nama_nasabah: str
    no_hp: str
    no_rekening: str
    nama_bank: str
    nama_pemilik_rekening: str
    alamat: Optional[str]
    foto_profil: Optional[str]
    saldo: Decimal
    is_active: bool
    tanggal_daftar: datetime

    class Config:
        from_attributes = True


class NasabahListResponse(BaseModel):
    total: int
    data: List[NasabahAdminResponse]


# ========== REQUEST: EDIT DATA NASABAH (data pribadi & rekening) ==========

class NasabahAdminUpdate(BaseModel):
    """Partial update — cuma field yang dikirim yang diubah. TIDAK termasuk saldo/is_active (endpoint sendiri)."""
    nama_nasabah: Optional[str] = Field(None, min_length=3, max_length=100)
    no_hp: Optional[str] = Field(None, pattern=r"^(\+62|0)[0-9]{9,12}$")
    no_rekening: Optional[str] = Field(None, min_length=10)
    nama_bank: Optional[str] = Field(None, min_length=3)
    nama_pemilik_rekening: Optional[str] = Field(None, min_length=3)
    alamat: Optional[str] = None
    foto_profil: Optional[str] = None


# ========== REQUEST: TOGGLE STATUS AKTIF ==========

class NasabahStatusUpdate(BaseModel):
    is_active: bool
    keterangan: Optional[str] = Field(None, description="Alasan nonaktif/aktifkan kembali (opsional, untuk catatan)")


# ========== REQUEST: KOREKSI SALDO MANUAL ==========

class SaldoAdjustment(BaseModel):
    """Admin bisa nambah (+) atau kurangi (-) saldo manual, WAJIB kasih keterangan untuk audit trail"""
    jumlah: Decimal = Field(..., decimal_places=2, description="Nilai penyesuaian. Positif = nambah, negatif = kurangi")
    keterangan: str = Field(..., min_length=5, description="Wajib diisi - alasan koreksi saldo (untuk audit)")

# ========== RESPONSE: RIWAYAT KOREKSI SALDO (ADMIN) ==========
class RiwayatSaldoAdjustmentResponse(BaseModel):
    id_adjustment: int
    nik: str
    id_admin: int
    jumlah: Decimal
    saldo_sebelum: Decimal
    saldo_sesudah: Decimal
    keterangan: str
    tanggal: datetime

    class Config:
        from_attributes = True