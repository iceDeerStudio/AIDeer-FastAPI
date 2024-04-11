from sqlmodel import SQLModel, Field, Relationship
from typing import List
from uuid import UUID
from enum import Enum


class PresetLikeRecord(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    preset_id: UUID = Field(foreign_key="preset.id", primary_key=True)
    user: "User" = Relationship(back_populates="liked_presets")
    preset: "Preset" = Relationship(back_populates="like_records")


class ChatLikeRecord(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    chat_id: UUID = Field(foreign_key="chat.id", primary_key=True)
    user: "User" = Relationship(back_populates="liked_chats")
    chat: "Chat" = Relationship(back_populates="like_records")


class LikesRead(SQLModel):
    preset_ids: List[UUID]
    chat_ids: List[UUID]


from .user import User
from .chat import Chat
from .preset import Preset

PresetLikeRecord.model_rebuild()
ChatLikeRecord.model_rebuild()
