from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal


class IoTBeratCreate(BaseModel):
    """Dikirim tim IoT: cuma berat. NIK & scan_id opsional."""
    machine_id: str = Field(..., min_length=1, max_length=50)
    berat: Decimal = Field(..., gt=0, decimal_places=2, description="Berat dalam KG")
    nik: Optional[str] = Field(None, min_length=16, max_length=16)
    scan_id: Optional[str] = Field(None, max_length=64)


class MLDeteksiCreate(BaseModel):
    """Dikirim tim ML: label hasil deteksi + confidence + foto."""
    machine_id: str = Field(..., min_length=1, max_length=50)
    jenis_terdeteksi: str = Field(..., min_length=1, max_length=100, description="Contoh: metal_can")
    confidence: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    foto_base64: Optional[str] = None
    nik: Optional[str] = Field(None, min_length=16, max_length=16)
    scan_id: Optional[str] = Field(None, max_length=64)


class ScanResponse(BaseModel):
    id: int
    machine_id: str
    status: str
    pesan: str
    id_transaksi: Optional[int] = None