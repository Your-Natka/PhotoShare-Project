"""
config.py — конфігураційні налаштування застосунку PhotoShare

Цей файл містить:
1. Параметри підключення до бази даних
2. Налаштування аутентифікації та JWT
3. Налаштування для відправки email
4. Параметри Redis для кешування
5. Конфігурацію Cloudinary для роботи з зображеннями
6. Функцію ініціалізації Cloudinary

Використовується Pydantic Settings для читання змінних середовища.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import cloudinary

class Settings(BaseSettings):
    # -------------------- DATABASE --------------------
    sqlalchemy_database_url: str = Field(
        ...,
        alias="SQLALCHEMY_DATABASE_URL",
        description="URL підключення до PostgreSQL бази даних"
    )

    # -------------------- AUTH --------------------
    secret_key: str = Field(..., alias="SECRET_KEY", description="Секретний ключ для JWT токенів")
    algorithm: str = Field(..., alias="ALGORITHM", description="Алгоритм підпису JWT токенів")
    access_token_expire_minutes: int = Field(..., alias="ACCESS_TOKEN_EXPIRE_MINUTES", description="Час життя access token у хвилинах")
    expire_minutes: int = Field(..., alias="EXPIRE_MINUTES", description="Загальний час життя токенів у хвилинах")

    # -------------------- MAIL --------------------
    mail_username: str = Field(..., alias="MAIL_USERNAME", description="Логін поштової скриньки для відправки листів")
    mail_password: str = Field(..., alias="MAIL_PASSWORD", description="Пароль від поштової скриньки")
    mail_from: str = Field(..., alias="MAIL_FROM", description="Email відправника")
    mail_port: int = Field(..., alias="MAIL_PORT", description="Порт SMTP сервера")
    mail_server: str = Field(..., alias="MAIL_SERVER", description="Адреса SMTP сервера")

    # -------------------- REDIS --------------------
    redis_url: str = Field(..., alias="REDIS_URL", description="URL підключення до Redis для кешування та чорного списку токенів")

    # -------------------- CLOUDINARY --------------------
    cloudinary_name: str = Field(..., alias="CLOUDINARY_NAME", description="Назва облікового запису Cloudinary")
    cloudinary_api_key: str = Field(..., alias="CLOUDINARY_API_KEY", description="API ключ для Cloudinary")
    cloudinary_api_secret: str = Field(..., alias="CLOUDINARY_API_SECRET", description="API секрет для Cloudinary")

    # -------------------- CONFIG --------------------
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="allow"  # дозволяє додаткові змінні середовища
    )


# Створення екземпляру налаштувань
settings = Settings()


def init_cloudinary():
    """
    Ініціалізація Cloudinary з параметрами з Settings.
    Після виклику цієї функції можна використовувати Cloudinary SDK для завантаження та трансформації зображень.
    """
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )