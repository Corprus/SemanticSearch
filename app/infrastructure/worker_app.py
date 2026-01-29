# app/infrastructure/worker_app.py
from celery import Celery
import os
from urllib.parse import quote
from database.config import get_settings

from database.database import init_db

import logging

logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/")

# vhost обязательно url-encode ("/" → "%2F")
RABBITMQ_URL = (
    f"amqp://{quote(RABBITMQ_USER)}:{quote(RABBITMQ_PASSWORD)}"
    f"@{RABBITMQ_HOST}:{RABBITMQ_PORT}/{quote(RABBITMQ_VHOST, safe='')}"
)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/")

# vhost обязательно url-encode ("/" → "%2F")
RABBITMQ_URL = (
    f"amqp://{quote(RABBITMQ_USER)}:{quote(RABBITMQ_PASSWORD)}"
    f"@{RABBITMQ_HOST}:{RABBITMQ_PORT}/{quote(RABBITMQ_VHOST, safe='')}"
)

init_db(get_settings())

# --- Celery app ---
worker_app = Celery(
    "semantic_search",
    broker=RABBITMQ_URL,
    backend=None,  # result backend не нужен, если не используешь .get()
)

worker_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,          # ack после выполнения (важно)
    worker_prefetch_multiplier=1, # меньше шансов потерять задачу при падении
)

worker_app.autodiscover_tasks(["infrastructure.worker_task"])
