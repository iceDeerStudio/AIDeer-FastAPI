from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List


class UserBase(SQLModel):
    username: str = Field(
        index=True,
        unique=True,
        max_length=50,
        min_length=2,
        title="Username",
    )
    permission: int = Field(
        default=1,
        title="User permission level",
        description="0: Visitor, 1: User, 2: Admin",
        ge=0,
        le=2,
    )
    nickname: Optional[str] = Field(
        default=None,
        nullable=True,
        max_length=50,
        min_length=1,
        title="User nickname",
    )


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    password_hash: Optional[str] = Field(nullable=True)
    wechat_openid: Optional[str] = Field(default=None, nullable=True)
    wechat_session_key: Optional[str] = Field(default=None, nullable=True)
    avatar: str = Field(
        default="/static/avatars/default.webp",
        max_length=255,
        min_length=10,
    )
    credit_records: List["CreditRecord"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    credits_left: int = Field(
        default=0,
        title="Credits left",
        description="The amount of credits left",
    )
    chats: List["Chat"] = Relationship(
        back_populates="owner", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    presets: List["Preset"] = Relationship(
        back_populates="owner", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    liked_presets: List["PresetLikeRecord"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    liked_chats: List["ChatLikeRecord"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class UserCreate(UserBase):
    password: str = Field(
        max_length=255,
        min_length=6,
        title="User password",
        description="The password of the user",
    )


class UserRead(UserBase):
    id: int = Field(title="User ID", description="User's unique identifier")
    avatar: str = Field(
        title="User avatar",
        description="Url of user's avatar",
    )
    credits_left: int = Field(
        title="Credits left",
        description="The amount of credits left",
    )


# Import Models
from .credit import CreditRecord
from .chat import Chat
from .preset import Preset
from .like import PresetLikeRecord, ChatLikeRecord

# Rebuild Models
User.model_rebuild()
