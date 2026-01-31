FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["celery", "-A", "worker_app:worker_app", "worker", "--loglevel=INFO"]
