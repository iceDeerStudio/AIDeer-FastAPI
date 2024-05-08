from app.core.connections.sql import sqlalchemy_engine
from app.core.managers.message import MessageStorage
from app.core.managers.task import TaskManager
from app.core.managers.credit import CreditManager
from app.core.managers.client import ChatGenerationClientManager
from app.core.tasks.base_task import BaseTask
from app.models.chat import Chat
from app.models.message import Message, MessageRole, MessageType
from app.models.preset import PresetParameters
from app.models.task import TaskStatus, TaskFinish
from app.core.config import config
from sqlmodel import Session


class TitleGenerationTask(BaseTask):
    chat_id: str
    user_id: int

    async def on_finish(self, task_finish: TaskFinish):
        await super().on_finish(task_finish)
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

        client = ChatGenerationClientManager.get_client(
            preset_params.get_model_provider()
        )

        await self.on_status(TaskStatus.pending)

        await client.run_generate(
            messages=messages,
            preset_params=preset_params,
            status_callback=self.on_status,
            finish_callback=self.on_finish,
        )
