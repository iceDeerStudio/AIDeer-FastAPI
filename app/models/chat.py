from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum


class ChatVisibility(str, Enum):
    private = "private"
    shared = "shared"


class ChatBase(SQLModel):
    preset_id: UUID = Field(
        title="Preset ID",
        description="Preset's unique identifier",
        foreign_key="preset.id",
    )
    title: str = Field(
        max_length=50,
        min_length=1,
        title="Chat title",
        description="The title of the chat",
    )
    visibility: ChatVisibility = Field(
        default=ChatVisibility.private,
        title="Chat visibility",
        description="The visibility of the chat. ('private', 'shared')",
    )


class Chat(ChatBase, table=True):
    id: Optional[UUID] = Field(default=uuid4(), primary_key=True)
    owner_id: int = Field(
        title="Owner ID", description="Owner's unique identifier", foreign_key="user.id"
    )
    owner: "User" = Relationship(back_populates="chats")
    preset: "Preset" = Relationship()
    create_time: datetime = Field(default=datetime.now())
    update_time: datetime = Field(default=datetime.now())


class ChatCreate(ChatBase):
    messages: "Messages" = Field(title="Messages", description="Messages in the chat")


class ChatRead(ChatBase):
    id: UUID = Field(title="Chat ID", description="Chat's unique identifier")
    owner_id: int = Field(title="Owner ID", description="Owner's unique identifier")
    messages: "Messages" = Field(title="Messages", description="Messages in the chat")
    create_time: datetime = Field(
        title="Create time", description="The time when the chat is created"
    )
    update_time: datetime = Field(
        title="Update time", description="The time when the chat is updated"
    )


# Import Models
from .message import Messages
from .user import User
from .preset import Preset

# Rebuild Models
Chat.model_rebuild()
ChatCreate.model_rebuild()
ChatRead.model_rebuild()
