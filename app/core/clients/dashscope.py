from app.core.connections.rabbitmq import get_rabbitmq_connection
from app.core.config import config
from aio_pika.abc import (
    AbstractChannel,
    AbstractExchange,
    AbstractQueue,
)
from app.models.dashscope import (
    ChatGenerationRequest,
    ChatGenerationResponse,
    ChatGenerationParameters,
    ChatGenerationMessage,
    ChatGenerationInput,
    ChatGenerationModel,
    ChatGenerationFinishReason,
)
from app.core.managers.task import TaskManager, TaskStatus
from app.models.message import Message
from app.models.chat import Chat
from app.models.preset import PresetParameters
from app.models.task import TaskStream, TaskStatus
from app.core.managers.message import MessageStorage
from app.core.managers.credit import CreditManager
from app.core.connections.sql import sqlalchemy_engine
from app.core.config import config
from sqlmodel import Session
import aio_pika
import aiohttp


class ChatGeneration:
    api_key: str
    user_id: int
    task_id: str
    chat_id: str
    base_url: str
    channel: AbstractChannel
    exchange: AbstractExchange
    queue: AbstractQueue

    def __init__(
        self,
        user_id: int,
        task_id: str,
        chat_id: str,
        base_url: str = config.dashscope_base_url,
        api_key: str = config.dashscope_api_key,
    ):
        self.user_id = user_id
        self.task_id = task_id
        self.chat_id = chat_id
        self.base_url = base_url
        self.api_key = api_key

    async def __aenter__(self):
        await self.init_rabbitmq()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close_rabbitmq()

    async def build_request(self):
        with Session(sqlalchemy_engine) as session:
            chat = session.get(Chat, self.chat_id)
            preset = chat.preset

        preset_messages = MessageStorage.get_messages(chat.preset_id)
        chat_messages = MessageStorage.get_messages(self.chat_id)

        preset_params = PresetParameters.model_validate_json(preset.parameters)
        model = ChatGenerationModel(preset_params.model)
        params = ChatGenerationParameters.model_validate(preset_params.model_dump())
        input = ChatGenerationInput(
            messages=[
                ChatGenerationMessage.model_validate(message.model_dump())
                for message in preset_messages + chat_messages
            ]
        )

        request = ChatGenerationRequest(
            model=model,
            input=input,
            parameters=params,
        )

        return request

    async def init_rabbitmq(self):
        # Initialize RabbitMQ
        self.connection = await get_rabbitmq_connection()
        self.channel = await self.connection.channel()
        self.queue = await self.channel.declare_queue(f"streaming_{self.task_id}")
        self.exchange = await self.channel.declare_exchange(
            "streaming", aio_pika.ExchangeType.DIRECT
        )
        await self.queue.bind(self.exchange, routing_key=f"streaming_{self.task_id}")

    async def close_rabbitmq(self):
        # Close RabbitMQ
        await self.queue.unbind(self.exchange, routing_key=f"streaming_{self.task_id}")
        await self.channel.close()

    async def run(self):
        async with self:
            # Set Task Status
            TaskManager.set_task(self.task_id, TaskStatus.running)

            # Build Text Generation Request
            request = await self.build_request()

            # Request Text Generation
            await self.send_request(request)

    async def send_request(self, data: ChatGenerationRequest, enable_sse: bool = True):
        url = f"{self.base_url}/services/aigc/text-generation/generation"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if enable_sse:
            headers["X-DashScope-SSE"] = "enable"

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(
                url, data=data.model_dump_json(exclude_none=True)
            ) as resp:
                if resp.status == 200:
                    async for line in resp.content:
                        event = line.decode("utf-8").strip()
                        if event.startswith("data:"):
                            event = event[5:]
                            await self.on_event(event)
                else:
                    await self.on_failure(resp)

    async def on_event(self, event):
        response = ChatGenerationResponse.model_validate_json(event)
        await self.exchange.publish(
            aio_pika.Message(
                body=TaskStream(
                    task_id=self.task_id,
                    status=TaskStatus.running,
                    content=response.output.choices[0].message.content,
                )
                .model_dump_json()
                .encode("utf-8"),
            ),
            routing_key=f"streaming_{self.task_id}",
            mandatory=True,
        )
        if response.output.choices[0].finish_reason != ChatGenerationFinishReason.null:
            await self.on_finish(response)

    async def on_finish(self, response: ChatGenerationResponse):
        await self.exchange.publish(
            aio_pika.Message(
                body=TaskStream(
                    task_id=self.task_id,
                    status=TaskStatus.finished,
                    content="Text Generation Complete",
                )
                .model_dump_json()
                .encode("utf-8"),
            ),
            routing_key=f"streaming_{self.task_id}",
        )
        MessageStorage.add_message(
            chat_id=self.chat_id,
            message=Message.model_validate(
                {
                    **response.output.choices[0].message.model_dump(),
                    "type": "text",
                }
            ),
        )
        CreditManager.consume_credit(
            self.user_id,
            response.usage.total_tokens,
            f"Chat Generation: {self.chat_id}",
        )
        TaskManager.set_task(self.task_id, TaskStatus.finished)

    async def on_failure(self, resp: aiohttp.ClientResponse):
        print(f"Text Generation Request Failed: {resp.status}, {await resp.text()}")
        await self.exchange.publish(
            aio_pika.Message(
                body=TaskStream(
                    task_id=self.task_id,
                    status=TaskStatus.failed,
                    content=f"Text Generation Request Failed: {resp.status}",
                )
                .model_dump_json()
                .encode("utf-8"),
            ),
            routing_key=f"streaming_{self.task_id}",
        )
        raise Exception(f"Text Generation Request Failed: {resp.status}")
