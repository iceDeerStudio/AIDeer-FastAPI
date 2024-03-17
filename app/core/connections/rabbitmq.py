import aio_pika
from aio_pika.abc import AbstractConnection
from app.core.config import config


connection: AbstractConnection = None


async def get_rabbitmq_connection() -> AbstractConnection:
    global connection
    if connection is None:
        connection = await aio_pika.connect_robust(config.rabbitmq_url)
    return connection
