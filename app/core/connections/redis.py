from redis import Redis
from app.core.config import config

redis_client = Redis(
    host=config.redis_host,
    port=config.redis_port,
    db=config.redis_db,
    password=config.redis_password,
    encoding="utf-8",
    decode_responses=True,
)
