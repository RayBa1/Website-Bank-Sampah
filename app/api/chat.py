from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Header, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import asc

from app.core.database import get_db
from app.models.models import PesanChat
from app.schemas.chat import PesanChatResponse
from app.utils.security import get_current_nasabah, get_current_admin, get_session
from app.utils.chat_manager import manager

router = APIRouter(prefix="/chat", tags=["Livechat"])


# ---------- WebSocket: Nasabah ----------
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
    except WebSocketDisconnect:
        manager.disconnect_nasabah(nik)


# ---------- WebSocket: Admin (buka chat nasabah tertentu) ----------
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
                nik_nasabah=nik, sender_type="admin",
                sender_id=admin_username, isi_pesan=data["isi_pesan"]
            )
            db.add(pesan)
            db.commit()
            db.refresh(pesan)

            payload = PesanChatResponse.model_validate(pesan).model_dump(mode="json")
            await manager.send_to_nasabah(nik, payload)
    except WebSocketDisconnect:
        manager.disconnect_admin(nik, websocket)


# ---------- REST: riwayat chat (buat load pertama kali / pagination) ----------
@router.get("/history/{nik}", response_model=list[PesanChatResponse])
def get_chat_history(
    nik: str,
    authorization: str = Header(None),
    limit: int = 50,
    db: Session = Depends(get_db),
):
    get_current_admin(authorization)  # cuma admin yang butuh akses via nik orang lain
    return (
        db.query(PesanChat)
        .filter(PesanChat.nik_nasabah == nik)
        .order_by(asc(PesanChat.created_at))
        .limit(limit)
        .all()
    )


@router.get("/history-nasabah", response_model=list[PesanChatResponse])
def get_own_chat_history(
    authorization: str = Header(None),
    limit: int = 50,
    db: Session = Depends(get_db),
):
    nik = get_current_nasabah(authorization)
    return (
        db.query(PesanChat)
        .filter(PesanChat.nik_nasabah == nik)
        .order_by(asc(PesanChat.created_at))
        .limit(limit)
        .all()
    )