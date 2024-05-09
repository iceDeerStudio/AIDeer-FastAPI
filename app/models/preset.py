from sqlmodel import SQLModel, Field, Relationship, func
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum
import random


class PresetType(str, Enum):
    chat_generation = "chat_generation"
    image_generation = "image_generation"


class PresetVisibility(str, Enum):
    private = "private"
    unlisted = "unlisted"
    public = "public"


class PresetModel(str, Enum):
    qwen_turbo = "qwen-turbo"
    qwen_plus = "qwen-plus"
    qwen_max = "qwen-max"
    qwen_max_1201 = "qwen-max-1201"
    qwen_max_longcontext = "qwen-max-longcontext"
    deepseek_chat = "deepseek-chat"
    gpt_3_5_turbo = "gpt-3.5-turbo"


class PresetParameters(SQLModel):
    model: Optional[PresetModel] = Field(
        default=PresetModel.deepseek_chat,
        title="Model name",
        description="Model to use for generation",
    )
    seed: Optional[int] = Field(
        default=random.randint(0, 2**63 - 1),
        ge=0,
        le=2**63 - 1,
        title="Random seed",
        description="Random seed for generation",
    )
    max_tokens: Optional[int] = Field(
        default=1500,
        gt=0,
        le=2000,
        title="Max tokens",
        description="Maximum number of tokens to generate",
    )
    top_p: Optional[float] = Field(
        default=0.5, gt=0, lt=1, title="Top p", description="Top p for nucleus sampling"
    )
    top_k: Optional[int] = Field(
        default=None,
        gt=0,
        le=100,
        title="Top k",
        description="Top k for nucleus sampling",
    )
    repetition_penalty: Optional[float] = Field(
        default=1.1,
        ge=0,
        title="Repetition penalty",
        description="Repetition penalty for generation",
    )
    frequency_penalty: Optional[float] = Field(
        default=0,
        ge=-2,
        le=2,
        title="Frequency penalty",
        description="Frequency penalty for generation",
    )
    presence_penalty: Optional[float] = Field(
        default=0,
        ge=-2,
        le=2,
        title="Presence penalty",
        description="Presence penalty for generation",
    )
    temperature: Optional[float] = Field(
        default=0.85,
        ge=0,
        lt=2,
        title="Temperature",
        description="Temperature for generation",
    )

    def get_token_cost_multiplier(self):
        if self.model == PresetModel.deepseek_chat:
            return 1
        elif self.model == PresetModel.qwen_turbo:
            return 4
        elif self.model == PresetModel.qwen_plus:
            return 10
        elif self.model == PresetModel.gpt_3_5_turbo:
            return 11
        elif self.model == PresetModel.qwen_max:
            return 60
        else:
            raise ValueError("Invalid model")

    def get_model_provider(self):
        if self.model in [
            PresetModel.qwen_turbo,
            PresetModel.qwen_plus,
            PresetModel.qwen_max,
            PresetModel.qwen_max_1201,
            PresetModel.qwen_max_longcontext,
        ]:
            return "dashscope"
        elif self.model == PresetModel.deepseek_chat:
            return "deepseek"
        elif self.model == PresetModel.gpt_3_5_turbo:
            return "openai"
        else:
            raise ValueError("Invalid model")


class PresetBase(SQLModel):
    title: str = Field(
        max_length=50,
        min_length=1,
        title="Preset title",
        description="The name of the preset",
    )
    description: Optional[str] = Field(
        default=None,
        nullable=True,
        max_length=255,
        min_length=1,
        title="Preset description",
    )
    type: PresetType = Field(
        default=PresetType.chat_generation,
        title="Preset type",
        description="The type of the preset. ('chat_generation', 'image_generation')",
    )
    visibility: PresetVisibility = Field(
        default=PresetVisibility.private,
        title="Preset visibility",
        description="The visibility of the preset. ('private', 'unlisted', 'public')",
    )


class Preset(PresetBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    owner_id: int = Field(
        title="Owner ID", description="Owner's unique identifier", foreign_key="user.id"
    )
    owner: "User" = Relationship(back_populates="presets")
    parameters: Optional[str] = Field(
        default=None, title="Preset parameters", description="Parameters of the preset"
    )
    like_records: List["PresetLikeRecord"] = Relationship(
        back_populates="preset",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    chats_used: List["Chat"] = Relationship(
        back_populates="preset",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    create_time: datetime = Field(default_factory=datetime.now)
    update_time: datetime = Field(
        default_factory=datetime.now, sa_column_kwargs={"onupdate": func.now()}
    )


class PresetCreate(PresetBase):
    messages: "Messages" = Field(title="Messages", description="Messages in the preset")
    parameters: "PresetParameters" = Field(
        default=None, title="Preset parameters", description="Parameters of the preset"
    )


class PresetRead(PresetBase):
    id: UUID = Field(title="Preset ID", description="Preset's unique identifier")
    owner_id: int = Field(title="Owner ID", description="Owner's unique identifier")
    messages: "Messages" = Field(title="Messages", description="Messages in the preset")
    parameters: Optional[PresetParameters] = Field(
        default=None, title="Preset parameters", description="Parameters of the preset"
    )
    create_time: datetime = Field(
        title="Create time", description="The time when the preset is created"
    )
    update_time: datetime = Field(
        title="Update time", description="The time when the preset is updated"
    )


# Import Models
from .message import Messages
from .user import User
from .chat import Chat
from .like import PresetLikeRecord

# Rebuild Models
Preset.model_rebuild()
PresetRead.model_rebuild()
