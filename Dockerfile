# Використовуємо Python 3.12
FROM python:3.12-slim

# Встановлюємо робочу директорію
WORKDIR /app

# Встановлюємо залежності для системних пакетів (якщо потрібні)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копіюємо файли проєкту
COPY ./app ./app
COPY requirements.txt ./requirements.txt
COPY alembic ./alembic


# Встановлюємо Python-залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

# Порт, на якому буде працювати FastAPI
EXPOSE 8080

# Команда запуску FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]