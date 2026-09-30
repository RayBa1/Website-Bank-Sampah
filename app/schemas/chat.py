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

class ChatConversationResponse(BaseModel):
    nik_nasabah: str
    nama_nasabah: str | None = None
    last_message: str | None = None
    last_message_at: datetime | None = None
    last_sender_type: str | None = None
    unread_count: int = 0
    handled_by: str | None = None

class ChatAssignmentResponse(BaseModel):
    nik_nasabah: str
    admin_username: str
    claimed_at: datetime

    class Config:
        from_attributes = True