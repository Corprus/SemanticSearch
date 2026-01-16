# app/main.py

import os
from fastapi import FastAPI
from health import router as health_router

app = FastAPI(title="Semantic Search Service")

app.include_router(health_router)

HOST = os.getenv("APP_HOST", "0.0.0.0")
PORT = int(os.getenv("APP_PORT", "8000"))

# Для uvicorn запускается командой ниже через docker (см. requirements)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)