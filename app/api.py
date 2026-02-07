import os
import time
import socket
import uvicorn
import logging

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from common.database.database import init_db, get_engine, Base
from common.config import get_settings

from routes.users import router as users_router
from routes.auth import router as auth_router
from routes.transactions import router as transactions_router
from routes.documents import router as documents_router
from routes.search import router as search_router
from routes.health import router as health_router

from common.exceptions import (
    ServiceException,
    InvalidCredentialsException,
    UserAlreadyExistsException,
    UserNotExistsException,
    InsufficientBalanceException,
    DocumentNotFoundException,
    AccessDeniedException,
    QueryNotFoundException
)

from infrastructure.initializer import init


logger = logging.getLogger(__name__)
settings = get_settings()

HOST = os.getenv("APP_HOST", "0.0.0.0")
PORT = int(os.getenv("APP_PORT", "8000"))
APP_NAME = os.getenv("APP_NAME", "Semantic Search")
from infrastructure.http_prefix_middleware import ForwardedPrefixMiddleware

def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    
    APP_NAME = os.getenv("APP_NAME", "Semantic Search")
    app = FastAPI(title=APP_NAME, root_path_in_servers=True)
    app.add_middleware(ForwardedPrefixMiddleware)
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(health_router)

    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(users_router, prefix="/users", tags=["users"])
    app.include_router(transactions_router, prefix="/transactions", tags=["transactions"])
    app.include_router(documents_router, prefix="/documents", tags=["documents"])
    app.include_router(search_router, prefix="/search", tags=["search"])
    app.include_router(health_router)

    return app

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
app = create_application()

@app.on_event("startup") 
def on_startup():
    try:
        drop_all = bool(os.getenv("DROP_DB", False))
        logger.info(f"Drop_db is {drop_all}")
        logger.info("Initializing database...")
        settings = get_settings()
        init_db(settings)
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        print(settings.APP_NAME)
        print(settings.API_VERSION)
        print(f'Debug: {settings.DEBUG}')
    
        print(settings.POSTGRES_HOST)
        print(settings.POSTGRES_DB)
        print(settings.POSTGRES_USER)
        wait_amqp()
        init(settings, drop_all)
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise
    
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Application shutting down...")

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    uvicorn.run(
        'api:app',
        host=HOST,
        port=PORT,
        reload=True,
#        root_path="/api",
        log_level="info"
    )

@app.exception_handler(ServiceException)
async def service_exception_handler(_, exc: ServiceException):
    if isinstance(exc, InvalidCredentialsException):
        code = status.HTTP_401_UNAUTHORIZED
        detail = "Invalid login or password"

    elif isinstance(exc, UserAlreadyExistsException):
        code = status.HTTP_409_CONFLICT
        detail = "User already exists"

    elif isinstance(exc, UserNotExistsException):
        code = status.HTTP_404_NOT_FOUND
        detail = "User not found"

    elif isinstance(exc, DocumentNotFoundException):
        code = status.HTTP_404_NOT_FOUND
        detail = "Document not found"

    elif isinstance(exc, QueryNotFoundException):
        code = status.HTTP_404_NOT_FOUND
        detail = "Query not found"

    elif isinstance(exc, AccessDeniedException):
        code = status.HTTP_403_FORBIDDEN
        detail = "Access denied"

    elif isinstance(exc, InsufficientBalanceException):
        code = status.HTTP_409_CONFLICT
        detail = "Insufficient balance"

    else:
        code = status.HTTP_400_BAD_REQUEST
        detail = "Service error"

    return JSONResponse(
        status_code=code,
        content={"detail": detail},
    )