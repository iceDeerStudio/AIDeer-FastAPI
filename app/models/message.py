from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import List
from enum import Enum
from pydantic import RootModel


class MessageType(str, Enum):
    text = "text"
    image = "image"


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class Message(SQLModel):
    role: MessageRole = Field(
        title="Role",
        description="The role of the sender. ('user', 'assistant', 'system')",
    )
    type: MessageType = Field(
        title="Message type",
        description="The type of the message. ('text', 'image')",
    )
    content: str = Field(
        title="Message content",
        description="The content of the message. (text or url)",
    )
    visibility: bool = Field(
        default=True,
        title="Visibility",
        description="The visibility of the message. (True: visible, False: hidden)",
    )
    create_time: datetime = Field(
        title="Create time",
        description="The time when the message is created",
        default=datetime.now(),
    )


class Messages(RootModel):
    root: List[Message] = Field(
        title="Messages", description="Messages in the chat or the preset"
    )

    def __add__(self, other: "Messages") -> "Messages":
        return Messages(root=self.root + other.root)

    def __iadd__(self, other: "Messages") -> "Messages":
        self.root += other.root
        return self

    def __len__(self) -> int:
        return len(self.root)

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, index: int) -> Message:
        return self.root[index]

    def __setitem__(self, index: int, value: Message):
        self.root[index] = value

    def __delitem__(self, index: int):
        del self.root[index]

    def append(self, value: Message):
        self.root.append(value)

    def extend(self, values: List[Message]):
        self.root.extend(values)

    def insert(self, index: int, value: Message):
        self.root.insert(index, value)

    def remove(self, value: Message):
        self.root.remove(value)

    def pop(self, index: int) -> Message:
        return self.root.pop(index)
