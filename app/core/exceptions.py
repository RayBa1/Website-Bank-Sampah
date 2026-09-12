from fastapi import HTTPException, status

class NasabahNotFound(HTTPException):
    def __init__(self):
        super().__init__(status_code=404, detail="Nasabah tidak ditemukan")

class InvalidCredentials(HTTPException):
    def __init__(self):
        super().__init__(status_code=401, detail="NIK atau password salah")

class DuplicateNIK(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="NIK sudah terdaftar")