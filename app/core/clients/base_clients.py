from app.models.message import Message
from app.models.preset import PresetParameters
from app.models.task import TaskStatus, TaskFinish, TaskStream
from typing import Callable, Awaitable


class ChatGenerationClient:
    status_callback: Callable[[TaskStatus], Awaitable[None]]
    finish_callback: Callable[[TaskFinish], Awaitable[None]]
    streaming_callback: Callable[[TaskStream], Awaitable[None]]

    def __init__(self):
        raise NotImplementedError

    async def run_generate(
        self,
        messages: list[Message],
        preset_params: PresetParameters,
        status_callback: Callable[[TaskStatus], None] = None,
        finish_callback: Callable[[TaskFinish], None] = None,
        streaming_callback: Callable[[TaskStream], None] = None,
    ):
        raise NotImplementedError
