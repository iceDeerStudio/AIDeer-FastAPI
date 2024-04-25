from app.core.config import config
from app.models.dashscope import (
    ChatGenerationRequest,
    ChatGenerationResponse,
    ChatGenerationParameters,
    ChatGenerationMessage,
    ChatGenerationInput,
    ChatGenerationModel,
    ChatGenerationFinishReason,
)
from app.models.message import Message
from app.models.preset import PresetParameters
from app.models.task import TaskStream, TaskStatus, TaskFinish
from app.core.log import logger
from app.core.config import config
from pydantic import ValidationError
from typing import Callable, Awaitable
import aiohttp


class ChatGeneration:
    api_key: str
    base_url: str
    status_callback: Callable[[TaskStatus], Awaitable[None]]
    finish_callback: Callable[[TaskFinish], Awaitable[None]]
    streaming_callback: Callable[[TaskStream], Awaitable[None]]

    def __init__(
        self,
        base_url: str = config.dashscope_base_url,
        api_key: str = config.dashscope_api_key,
    ):
        self.base_url = base_url
        self.api_key = api_key

    def build_request(
        self, messages: list[Message], preset_params: PresetParameters
    ) -> ChatGenerationRequest:
        model = ChatGenerationModel(preset_params.model)
        params = ChatGenerationParameters.model_validate(preset_params.model_dump())
        input = ChatGenerationInput(
            messages=[
                ChatGenerationMessage.model_validate(message.model_dump())
                for message in messages
            ]
        )
        request = ChatGenerationRequest(
            model=model,
            input=input,
            parameters=params,
        )
        return request

    async def run(
        self,
        messages: list[Message],
        preset_params: PresetParameters,
        status_callback: Callable[[TaskStatus], None] = None,
        finish_callback: Callable[[TaskFinish], None] = None,
        streaming_callback: Callable[[TaskStream], None] = None,
    ) -> str:
        self.status_callback = status_callback
        self.finish_callback = finish_callback
        self.streaming_callback = streaming_callback

        request = self.build_request(messages, preset_params)

        await self.send_request(
            request, enable_sse=True if streaming_callback else False
        )

    async def send_request(
        self,
        data: ChatGenerationRequest,
        enable_sse: bool = True,
    ):
        if self.status_callback:
            await self.status_callback(TaskStatus.running)
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
                if resp.status != 200:
                    self.on_failure(resp)
                    return
                if enable_sse:
                    async for line in resp.content:
                        event = line.decode("utf-8").strip()
                        if not event.startswith("data:"):
                            continue
                        event = event[5:]
                        if event.strip() == "":
                            continue
                        try:
                            event = ChatGenerationResponse.model_validate_json(event)
                        except ValidationError:
                            self.on_failure(resp)
                            return
                        await self.on_event(event)
                else:
                    event = await resp.json()
                    try:
                        event = ChatGenerationResponse.model_validate(event)
                    except ValidationError:
                        self.on_failure(resp, await resp.text())
                    await self.on_event(event)

    async def on_event(self, response: ChatGenerationResponse):
        if response.output.choices[0].finish_reason != ChatGenerationFinishReason.null:
            await self.on_finish(response)
        elif self.streaming_callback:
            await self.streaming_callback(
                TaskStream(
                    status=TaskStatus.running,
                    content=response.output.choices[0].message.content,
                )
            )

    async def on_finish(self, response: ChatGenerationResponse):
        if self.status_callback:
            await self.status_callback(TaskStatus.finished)
        if self.finish_callback:
            await self.finish_callback(
                TaskFinish(
                    status=TaskStatus.finished,
                    content=response.output.choices[0].message.content,
                    token_cost=response.usage.total_tokens,
                )
            )

    async def on_failure(self, resp: aiohttp.ClientResponse, event: str):
        logger.warning(
            (
                f"Text Generation Request Failed: {resp.status}, {event if event else await resp.text()}"
            )
        )
        if self.status_callback:
            self.status_callback(TaskStatus.failed)
