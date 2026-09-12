from fastapi import WebSocket

class ChatConnectionManager:
    def __init__(self):
        # satu nasabah biasanya cuma 1 koneksi aktif (device yang lagi buka chat)
        self.nasabah_connections: dict[str, WebSocket] = {}
        # satu nik bisa ditonton beberapa admin sekaligus (misal admin refresh/buka di 2 tab)
        self.admin_connections: dict[str, list[WebSocket]] = {}

    async def connect_nasabah(self, nik: str, ws: WebSocket):
        await ws.accept()
        self.nasabah_connections[nik] = ws

    def disconnect_nasabah(self, nik: str):
        self.nasabah_connections.pop(nik, None)

    async def connect_admin(self, nik: str, ws: WebSocket):
        await ws.accept()
        self.admin_connections.setdefault(nik, []).append(ws)

    def disconnect_admin(self, nik: str, ws: WebSocket):
        if nik in self.admin_connections:
            self.admin_connections[nik].remove(ws)
            if not self.admin_connections[nik]:
                del self.admin_connections[nik]

    async def send_to_nasabah(self, nik: str, data: dict):
        ws = self.nasabah_connections.get(nik)
        if ws:
            await ws.send_json(data)

    async def send_to_admins(self, nik: str, data: dict):
        for ws in self.admin_connections.get(nik, []):
            await ws.send_json(data)

manager = ChatConnectionManager()