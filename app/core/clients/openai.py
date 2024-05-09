from app.models.task import TaskStream, TaskStatus, TaskFinish
from app.models.preset import PresetParameters
from app.models.message import Message
from app.core.clients.base_clients import ChatGenerationClient
from app.core.config import config
from app.core.log import logger
from openai import AsyncOpenAI, APIError

from typing import List, Awaitable, Callable


class ChatGenerationOpenAIClient(ChatGenerationClient):
    api_key: str
    base_url: str
    client: AsyncOpenAI
    status_callback: Callable[[TaskStatus], Awaitable[None]]
    finish_callback: Callable[[TaskFinish], Awaitable[None]]
    streaming_callback: Callable[[TaskStream], Awaitable[None]]

    def __init__(
        self,
        api_key: str = config.openai_api_key,
        base_url: str = config.openai_base_url,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def run_generate(
        self,
        messages: List[Message],
        preset_params: PresetParameters,
        status_callback: Callable[[TaskStatus], Awaitable[None]] = None,
        finish_callback: Callable[[TaskFinish], Awaitable[None]] = None,
        streaming_callback: Callable[[TaskStream], Awaitable[None]] = None,
    ):
        self.status_callback = status_callback
        self.finish_callback = finish_callback
        self.streaming_callback = streaming_callback

        chat_messages = [
            {"role": message.role, "content": message.content} for message in messages
        ]

        try:
            response = await self.client.chat.completions.create(
                messages=chat_messages,
                stream=True if streaming_callback else False,
                **preset_params.model_dump(
                    exclude={"tok_k", "repetition_penalty"}, exclude_none=True
                ),
            )

            if streaming_callback is None:
                if response.choices[0].finish_reason not in [
                    "stop",
                    "length",
                    "content_filter",
                ]:
                    logger.error(
                        f"Unexpected finish reason: {response.choices[0].finish_reason}"
                    )
                    await self.status_callback(TaskStatus.failed)
                    return
                full_content = response.choices[0].message.content
                await self.finish_callback(
                    TaskFinish(
                        status=TaskStatus.finished,
                        content=full_content,
                        token_cost=response.usage.total_tokens,
                    )
                )
                return

            full_content = ""
            async for chunk in response:
                if chunk.choices[0].finish_reason in [
                    "stop",
                    "length",
                    "content_filter",
                ]:
                    full_content += chunk.choices[0].delta.content
                    await self.finish_callback(
                        TaskFinish(
                            status=TaskStatus.finished,
                            content=full_content,
                            token_cost=chunk.usage.total_tokens,
                        )
                    )
                    break
                elif chunk.choices[0].finish_reason in [None, "null"]:
                    full_content += chunk.choices[0].delta.content
                    await self.streaming_callback(
                        TaskStream(
                            status=TaskStatus.running,
                            content=full_content,
                        )
                    )
                else:
                    logger.error(
                        f"Unexpected finish reason: {chunk.choices[0].finish_reason}"
                    )
                    await self.status_callback(TaskStatus.failed)
        except APIError as e:
            logger.error(f"OpenAI API error, code: {e.code}, message: {e.message}")
            await self.status_callback(TaskStatus.failed)
