from pydantic import BaseModel
from datetime import datetime

class PesanChatResponse(BaseModel):
    id: int
    nik_nasabah: str
    sender_type: str
    sender_id: str | None
    isi_pesan: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class PesanChatCreate(BaseModel):
    isi_pesan: str