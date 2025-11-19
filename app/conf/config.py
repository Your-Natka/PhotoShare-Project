from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import cloudinary

class Settings(BaseSettings):
    # -------------------- DATABASE --------------------
    sqlalchemy_database_url: str = Field(..., alias="SQLALCHEMY_DATABASE_URL")

    # -------------------- AUTH --------------------
    secret_key: str = Field(..., alias="SECRET_KEY")
    algorithm: str = Field(..., alias="ALGORITHM")
    access_token_expire_minutes: int = Field(..., alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    expire_minutes: int = Field(..., alias="EXPIRE_MINUTES")

    # -------------------- MAIL --------------------
    mail_username: str = Field(..., alias="MAIL_USERNAME")
    mail_password: str = Field(..., alias="MAIL_PASSWORD")
    mail_from: str = Field(..., alias="MAIL_FROM")
    mail_port: int = Field(..., alias="MAIL_PORT")
    mail_server: str = Field(..., alias="MAIL_SERVER")

    # -------------------- REDIS --------------------
    redis_url: str = Field(..., alias="REDIS_URL")

    # -------------------- CLOUDINARY --------------------
    cloudinary_name: str = Field(..., alias="CLOUDINARY_NAME")
    cloudinary_api_key: str = Field(..., alias="CLOUDINARY_API_KEY")
    cloudinary_api_secret: str = Field(..., alias="CLOUDINARY_API_SECRET")

    # -------------------- CONFIG --------------------
    model_config = SettingsConfigDict(
        extra="allow"  # дозволяє додаткові змінні середовища
    )


settings = Settings()


def init_cloudinary():
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )
