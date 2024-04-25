from sqlmodel import SQLModel, Field
from typing import Optional
from enum import Enum


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    finished = "finished"
    failed = "failed"


class TaskType(str, Enum):
    chat_generation = "chat_generation"
    title_generation = "title_generation"
    image_generation = "image_generation"


class Task(SQLModel):
    task_id: str
    status: TaskStatus = Field(default=TaskStatus.pending)


class TaskCreate(SQLModel):
    chat_id: str
    type: TaskType


class TaskStream(SQLModel):
    status: TaskStatus
    content: Optional[str] = None


class TaskFinish(TaskStream):
    token_cost: int
