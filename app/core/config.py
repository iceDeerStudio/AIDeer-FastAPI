from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import base64
import os


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Project settings
    project_name: str = Field(default="AIDeer API")
    debug: bool = Field(default=True)

    # API settings
    api_base_url: str = Field(default="http://127.0.0.1:8000")
    api_version: str = Field(default="v1")
    api_prefix: str = Field(default="/api/v1")
    cors_origins: list[str] = Field(
        default=["http://localhost:8000", "http://127.0.0.1:8000"]
    )

    # SQL settings
    database_url: str = Field(default="sqlite:///./test.db")

    # Redis settings
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379, ge=0, le=65535)
    redis_password: str = ""
    redis_db: int = Field(default=0, ge=0, le=15)

    # RabbitMQ settings
    rabbitmq_url: str = Field(default="amqp://guest:guest@localhost/")

    # JWT settings
    jwt_secret: str = Field(default=base64.b64encode(os.urandom(32)).decode())
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expires: int = Field(default=60 * 24 * 3, ge=0)
    jwt_wechat_access_token_expires: int = Field(default=60 * 24, ge=0)
    jwt_refresh_token_expires: int = Field(default=60 * 24 * 90, ge=0)

    # WeChat Mini Program settings
    wechat_appid: str = ""
    wechat_secret: str = ""

    # Dashscope settings
    dashscope_base_url: str = Field(default="https://dashscope.aliyuncs.com/api/v1")
    dashscope_api_key: str = ""

    # Admin credentials
    admin_user: str = Field(default="admin", max_length=50, min_length=2)
    admin_passwd: str = Field(default="admin123", max_length=255, min_length=6)

    # Static files settings
    static_dir: str = Field(default="static")
    static_url: str = Field(default="/static")


config = Config()
