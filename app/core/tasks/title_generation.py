from app.core.connections.sql import sqlalchemy_engine
from app.core.clients.dashscope import ChatGeneration
from app.core.managers.message import MessageStorage
from app.core.managers.task import TaskManager
from app.core.managers.credit import CreditManager
from app.models.chat import Chat
from app.models.message import Message, MessageRole, MessageType
from app.models.preset import PresetParameters
from app.models.task import TaskStatus, TaskFinish
from app.core.config import config
from sqlmodel import Session
from uuid import uuid4


class TitleGenerationTask:
    task_id: str
    chat_id: str
    user_id: int

    def __init__(self):
        self.task_id = str(uuid4())

    async def on_status(self, status: TaskStatus):
        TaskManager.set_task(self.task_id, status)

    async def on_finish(self, task_finish: TaskFinish):
        TaskManager.set_task(self.task_id, task_finish.status)
        CreditManager.consume_credit(
            user_id=self.user_id,
            amount=task_finish.token_cost,
            description=f"Title generation, chat_id: {self.chat_id}, task_id: {self.task_id}",
        )

        with Session(sqlalchemy_engine) as session:
            chat = session.get(Chat, self.chat_id)
            chat.title = task_finish.content
            session.add(chat)
            session.commit()

    async def run(self, chat_id: str):
        self.chat_id = chat_id

        with Session(sqlalchemy_engine) as session:
            chat = session.get(Chat, self.chat_id)
            self.user_id = chat.owner_id

        preset_params = PresetParameters(max_tokens=100)

        chat_messages = MessageStorage.get_messages(self.chat_id)
        preset_messages = MessageStorage.get_messages(chat.preset_id)
        question_message = Message(
            role=MessageRole.user,
            type=MessageType.text,
            content=config.title_generation_prompt,
        )

        messages = preset_messages + chat_messages + [question_message]

        textgen = ChatGeneration()

        await self.on_status(TaskStatus.pending)

        await textgen.run(
            messages=messages,
            preset_params=preset_params,
            status_callback=self.on_status,
            finish_callback=self.on_finish,
        )
