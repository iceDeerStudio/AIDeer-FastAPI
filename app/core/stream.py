from typing import AsyncIterator
from app.core.connections.rabbitmq import get_rabbitmq_connection
from app.core.connections.redis import redis_client
from app.models.task import TaskStream, TaskStatus
from aio_pika.abc import (
    AbstractQueueIterator,
    AbstractConnection,
    AbstractChannel,
    AbstractQueue,
)
from fastapi import HTTPException, status
import asyncio


class TaskStreaming:
    task_id: str
    connection: AbstractConnection
    channel: AbstractChannel
    queue: AbstractQueue
    iter: AbstractQueueIterator

    def __init__(self, task_id: str):
        self.task_id = task_id

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def start(self):
        if redis_client.hget("streaming_locks", self.task_id) is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Task {self.task_id} is already being streamed",
            )
        redis_client.hset("streaming_locks", self.task_id, 1)
        self.connection = await get_rabbitmq_connection()
        self.channel = await self.connection.channel()
        self.queue = await self.channel.declare_queue(f"streaming_{self.task_id}")
        self.iter = self.queue.iterator()

    async def close(self):
        await self.iter.close()
        await self.queue.delete()
        await self.channel.close()
        redis_client.hdel("streaming_locks", self.task_id)

    async def iterator(self) -> AsyncIterator:
        async with self:
            yield "event: open\n\n"
            async for message in self.iter:
                async with message.process():
                    if message.body:
                        task_stream = TaskStream.model_validate_json(message.body)
                        yield f"data: {task_stream.model_dump_json()}\n\n"
                        await asyncio.sleep(0.2)
                        if (
                            task_stream.status == TaskStatus.finished
                            or task_stream.status == TaskStatus.failed
                        ):
                            break
            yield "event: close\n\n"
