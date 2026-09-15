from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import asc

from app.core.database import get_db
from app.models.models import PesanChat
from app.schemas.chat import PesanChatResponse
from app.utils.security import get_current_nasabah, get_current_admin, get_session
from app.utils.chat_manager import manager

router = APIRouter(prefix="/chat", tags=["Livechat"])


# ========== WEBSOCKET: NASABAH ==========
@router.websocket("/ws/nasabah")
async def ws_chat_nasabah(websocket: WebSocket, token: str = Query(...), db: Session = Depends(get_db)):
    session = get_session(token)
    if not session:
        await websocket.close(code=4401)
        return
    nik = session["sub"]

    await manager.connect_nasabah(nik, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            pesan = PesanChat(nik_nasabah=nik, sender_type="nasabah", isi_pesan=data["isi_pesan"])
            db.add(pesan)
            db.commit()
            db.refresh(pesan)

            payload = PesanChatResponse.model_validate(pesan).model_dump(mode="json")
            await manager.send_to_admins(nik, payload)
            # kirim balik konfirmasi ke pengirim juga, biar UI nasabah update instan
            await websocket.send_json(payload)
    except WebSocketDisconnect:
        manager.disconnect_nasabah(nik)


# ========== WEBSOCKET: ADMIN (buka chat nasabah tertentu) ==========
@router.websocket("/ws/admin/{nik}")
async def ws_chat_admin(websocket: WebSocket, nik: str, token: str = Query(...), db: Session = Depends(get_db)):
    session = get_session(token)
    if not session or session.get("role") not in ("admin", "super_admin"):
        await websocket.close(code=4401)
        return
    admin_username = session["sub"]

    await manager.connect_admin(nik, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            pesan = PesanChat(
                nik_nasabah=nik,
                sender_type="admin",
                sender_id=admin_username,
                isi_pesan=data["isi_pesan"],
            )
            db.add(pesan)
            db.commit()
            db.refresh(pesan)

            payload = PesanChatResponse.model_validate(pesan).model_dump(mode="json")
            await manager.send_to_nasabah(nik, payload)
            await websocket.send_json(payload)
    except WebSocketDisconnect:
        manager.disconnect_admin(nik, websocket)


# ========== REST: riwayat chat (load pertama kali / pagination) ==========
@router.get("/history/{nik}", response_model=list[PesanChatResponse])
def get_chat_history_admin(
    nik: str,
    authorization: str = Header(None),
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Admin lihat riwayat chat nasabah tertentu berdasarkan NIK."""
    get_current_admin(authorization)
    return (
        db.query(PesanChat)
        .filter(PesanChat.nik_nasabah == nik)
        .order_by(asc(PesanChat.created_at))
        .limit(limit)
        .all()
    )


@router.get("/history-nasabah", response_model=list[PesanChatResponse])
def get_chat_history_nasabah(
    authorization: str = Header(None),
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Nasabah lihat riwayat chat-nya sendiri."""
    nik = get_current_nasabah(authorization)
    return (
        db.query(PesanChat)
        .filter(PesanChat.nik_nasabah == nik)
        .order_by(asc(PesanChat.created_at))
        .limit(limit)
        .all()
    )