from sqlmodel import SQLModel, Field, Relationship, func
from typing import Optional, List
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
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    owner_id: int = Field(
        title="Owner ID", description="Owner's unique identifier", foreign_key="user.id"
    )
    owner: "User" = Relationship(back_populates="chats")
    preset: "Preset" = Relationship(back_populates="chats_used")
    like_records: List["ChatLikeRecord"] = Relationship(
        back_populates="chat", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    create_time: datetime = Field(default_factory=datetime.now)
    update_time: datetime = Field(
        default_factory=datetime.now, sa_column_kwargs={"onupdate": func.now()}
    )


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
from .like import ChatLikeRecord

# Rebuild Models
Chat.model_rebuild()
ChatCreate.model_rebuild()
ChatRead.model_rebuild()
