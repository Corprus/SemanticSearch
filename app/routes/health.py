# app/health.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/health", summary="Проверка работоспособности сервиса")
def health():
    return {"status": "ok"}
