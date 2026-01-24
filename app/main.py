# app/main.py

import os
from fastapi import FastAPI
from health import router as health_router
from database.config import get_settings
from infrastructure.initializer import init

app = FastAPI(title="Semantic Search Service")

app.include_router(health_router)

HOST = os.getenv("APP_HOST", "0.0.0.0")
PORT = int(os.getenv("APP_PORT", "8000"))


# Для uvicorn запускается командой ниже через docker (см. requirements)
if __name__ == "__main__":

    settings = get_settings()
    print(settings.APP_NAME)
    print(settings.API_VERSION)
    print(f'Debug: {settings.DEBUG}')
    
    print(settings.POSTGRES_HOST)
    print(settings.POSTGRES_DB)
    print(settings.POSTGRES_USER)
    
    init(settings, drop_all=True)