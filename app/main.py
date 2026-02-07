# app/main.py

import os
from fastapi import FastAPI
from routes.health import router as health_router
from common.config import get_settings
from infrastructure.initializer import init

import time
import socket

app = FastAPI(title="Semantic Search Service")

app.include_router(health_router)

HOST = os.getenv("APP_HOST", "0.0.0.0")
PORT = int(os.getenv("APP_PORT", "8000"))

def wait_amqp():
    print("== Checking and waiting AMQP ==")
    host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    port = int(os.getenv("RABBITMQ_PORT", "5672"))
    deadline = time.time() + 20  # 20 секунд
    while time.time() < deadline:
        try:
            s = socket.socket()
            s.settimeout(2)
            s.connect((host, port))
            s.close()   
            return
        except OSError:
            time.sleep(2)
    print("== AMQP UP ==")         
    raise RuntimeError(f"RabbitMQ AMQP not reachable at {host}:{port}")

# Для uvicorn запускается командой ниже через docker (см. requirements)
if __name__ == "__main__":

    settings = get_settings()
    print(settings.APP_NAME)
    print(settings.API_VERSION)
    print(f'Debug: {settings.DEBUG}')
    
    print(settings.POSTGRES_HOST)
    print(settings.POSTGRES_DB)
    print(settings.POSTGRES_USER)
    drop_all = bool(os.getenv("DROP_DB", False))
    print(f"Drop_db is {drop_all}")
    wait_amqp()
    init(settings, drop_all=drop_all)