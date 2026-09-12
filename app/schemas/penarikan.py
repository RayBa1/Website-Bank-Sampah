from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum
from decimal import Decimal

class StatusPenarikanEnum(str, Enum):
    menunggu = "menunggu"
    disetujui = "disetujui"
    ditolak = "ditolak"
    selesai = "selesai"

# ========== REQUEST SCHEMAS ==========

class PenarikanSaldoCreate(BaseModel):
    jumlah: Decimal = Field(..., gt=0, decimal_places=2, description="Nominal yang ingin ditarik")
    keterangan: Optional[str] = None

# ========== RESPONSE SCHEMAS ==========

class PenarikanSaldoResponse(BaseModel):
    id_penarikan: int
    nik: str
    tanggal_pengajuan: datetime
    jumlah: Decimal
    status: StatusPenarikanEnum
    keterangan: Optional[str]
    tanggal_diproses: Optional[datetime]

    class Config:
        from_attributes = True