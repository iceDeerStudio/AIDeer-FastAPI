from sqlmodel import SQLModel, Field


class ServerMessage(SQLModel):
    message: str


class ExceptionDetail(SQLModel):
    detail: str | dict | None = Field(default=None)
