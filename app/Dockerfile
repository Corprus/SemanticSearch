FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# --- Для разработки: исходники подключаются volume ---
# --- Для прода: загружаем исходники прямо в образ, надо закомментить в docker-compose и раскомментить тут ---
# COPY . /app/

EXPOSE 8000

CMD ["python", "app/api.py"]

#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
