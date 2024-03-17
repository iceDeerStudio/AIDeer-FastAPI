from sqlmodel import SQLModel, Field
from typing import Optional
from enum import Enum


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    finished = "finished"
    failed = "failed"


class Task(SQLModel):
    task_id: str
    status: TaskStatus = Field(default=TaskStatus.pending)


class TaskCreate(SQLModel):
    chat_id: str


class TaskStream(SQLModel):
    task_id: str
    status: TaskStatus
    content: Optional[str] = None
