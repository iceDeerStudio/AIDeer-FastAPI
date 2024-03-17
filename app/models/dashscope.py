from sqlmodel import SQLModel, Field
from typing import Optional, List
from enum import Enum


class ChatGenerationModel(str, Enum):
    qwen_turbo = "qwen-turbo"
    qwen_plus = "qwen-plus"
    qwen_max = "qwen-max"
    qwen_max_1201 = "qwen-max-1201"
    qwen_max_longcontext = "qwen-max-longcontext"


class ChatGenerationRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class ChatGenerationFinishReason(str, Enum):
    stop = "stop"
    length = "length"
    null = "null"


class ChatGenerationResultFormat(str, Enum):
    message = "message"
    text = "text"


class ChatGenerationMessage(SQLModel):
    role: ChatGenerationRole
    content: str


class ChatGenerationInput(SQLModel):
    messages: List[ChatGenerationMessage]


class ChatGenerationParameters(SQLModel):
    result_format: Optional[ChatGenerationResultFormat] = (
        ChatGenerationResultFormat.message
    )
    seed: Optional[int] = Field(ge=0, le=2**64 - 1)
    max_tokens: Optional[int] = Field(gt=0, le=2000)
    top_p: Optional[float] = Field(gt=0, lt=1)
    top_k: Optional[int] = Field(gt=0, le=100)
    repetition_penalty: Optional[float] = Field(ge=0)
    temperature: Optional[float] = Field(ge=0, lt=2)
    stop: Optional[str | List[str] | List[int] | List[List[int]]] = None
    enable_search: Optional[bool] = None
    incremental_output: Optional[bool] = None


class ChatGenerationRequest(SQLModel):
    model: ChatGenerationModel
    input: ChatGenerationInput
    parameters: Optional[ChatGenerationParameters]


class ChatGenerationChoice(SQLModel):
    message: ChatGenerationMessage
    finish_reason: Optional[ChatGenerationFinishReason]


class ChatGenerationOutput(SQLModel):
    choices: List[ChatGenerationChoice]


class ChatGenerationUsage(SQLModel):
    total_tokens: int
    output_tokens: int
    input_tokens: int


class ChatGenerationResponse(SQLModel):
    output: ChatGenerationOutput
    usage: ChatGenerationUsage
    request_id: str
