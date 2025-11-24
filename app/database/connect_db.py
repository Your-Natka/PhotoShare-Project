"""
connect_db.py — налаштування підключення до бази даних для PhotoShare API.

Містить:
- Підключення до PostgreSQL через SQLAlchemy
- Створення об'єкта сесії для роботи з базою
- Базовий клас для моделей
- Функцію-залежність get_db для FastAPI
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

from app.conf.config import settings

# -------------------- DATABASE URL --------------------
SQLALCHEMY_DATABASE_URL = settings.sqlalchemy_database_url

# -------------------- ENGINE --------------------
# Створюємо SQLAlchemy engine для підключення до бази даних
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    echo=True,         # Логування всіх SQL-запитів
    pool_pre_ping=True # Перевірка доступності з'єднання перед використанням
)

# -------------------- SESSION --------------------
# Створюємо фабрику сесій для роботи з базою даних
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# -------------------- BASE MODEL --------------------
# Базовий клас для всіх моделей SQLAlchemy
Base = declarative_base()

# -------------------- DEPENDENCY --------------------
def get_db():
    """
    FastAPI dependency для отримання сесії бази даних.

    Використання:
        async def endpoint(db: Session = Depends(get_db)):
            ...

    Повертає об'єкт сесії SQLAlchemy, який закривається після використання.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
