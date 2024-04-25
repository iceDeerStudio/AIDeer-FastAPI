from app.core.connections.rabbitmq import get_rabbitmq_connection
from app.core.connections.sql import sqlalchemy_engine
from app.core.managers.task import TaskManager
from app.core.managers.credit import CreditManager
from app.core.managers.message import MessageStorage
from app.core.clients.dashscope import ChatGeneration
from app.models.task import TaskStatus, TaskFinish, TaskStream
from app.models.chat import Chat
from app.models.preset import PresetParameters
from app.models.message import Message, MessageRole, MessageType
from aio_pika.abc import (
    AbstractChannel,
    AbstractExchange,
    AbstractQueue,
)
from sqlmodel import Session
from uuid import uuid4
import aio_pika


class ChatGenerationTask:
    task_id: str
    chat_id: str
    user_id: int
    token_cost_multiplier: float
    exchange: AbstractExchange
    channel: AbstractChannel
    queue: AbstractQueue

    def __init__(self):
        self.task_id = str(uuid4())

    async def __aenter__(self):
        await self.init_rabbitmq()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close_rabbitmq()

    async def init_rabbitmq(self):
        # Initialize RabbitMQ
        connection = await get_rabbitmq_connection()
        self.channel = await connection.channel()
        self.queue = await self.channel.declare_queue(f"streaming_{self.task_id}")
        self.exchange = await self.channel.declare_exchange(
            "streaming", aio_pika.ExchangeType.DIRECT
        )
        await self.queue.bind(self.exchange, routing_key=f"streaming_{self.task_id}")

    async def close_rabbitmq(self):
        # Close RabbitMQ
        await self.queue.unbind(self.exchange, routing_key=f"streaming_{self.task_id}")
        await self.channel.close()

    async def on_status(self, status: TaskStatus):
        TaskManager.set_task(self.task_id, status)

    async def on_finish(self, task_finish: TaskFinish):
        await self.exchange.publish(
            aio_pika.Message(
                body=task_finish.model_dump_json().encode(encoding="utf-8")
            ),
            routing_key=f"streaming_{self.task_id}",
        )
        TaskManager.set_task(self.task_id, TaskStatus.finished, task_finish)
        CreditManager.consume_credit(
            user_id=self.user_id,
            amount=task_finish.token_cost * self.token_cost_multiplier,
            description=f"Chat generation, chat_id: {self.chat_id}, task_id: {self.task_id}",
        )
        MessageStorage.add_message(
            self.chat_id,
            Message(
                role=MessageRole.assistant,
                type=MessageType.text,
                content=task_finish.content,
            ),
        )

    async def on_stream(self, task_stream: TaskStream):
        await self.exchange.publish(
            aio_pika.Message(
                body=task_stream.model_dump_json().encode(encoding="utf-8")
            ),
            routing_key=f"streaming_{self.task_id}",
        )

    async def run(self, chat_id: str):
        self.task_id = str(uuid4())
        self.chat_id = chat_id

        with Session(sqlalchemy_engine) as session:
            chat = session.get(Chat, chat_id)
            if chat is None:
                raise ValueError("Chat not found")
            self.user_id = chat.owner_id
            preset_params = PresetParameters.model_validate_json(chat.preset.parameters)

        self.token_cost_multiplier = preset_params.get_token_cost_multiplier()

        chat_messages = MessageStorage.get_messages(chat_id)
        preset_messages = MessageStorage.get_messages(chat.preset_id)
        messages = preset_messages + chat_messages

        chat_generation = ChatGeneration()

        async with self:
            await self.on_status(TaskStatus.pending)

            try:
                await chat_generation.run(
                    messages=messages,
                    preset_params=preset_params,
                    status_callback=self.on_status,
                    finish_callback=self.on_finish,
                    streaming_callback=self.on_stream,
                )
            except Exception as e:
                await self.on_status(TaskStatus.failed)
                raise e
