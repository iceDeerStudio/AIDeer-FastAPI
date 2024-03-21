from sqlmodel import SQLModel, Field
from typing import Optional


class PasswordUpdate(SQLModel):
    old_password: Optional[str] = Field(
        default=None,
        max_length=255,
        min_length=6,
        title="Old password",
        description="The old password of the user",
    )
    new_password: str = Field(
        max_length=255,
        min_length=6,
        title="New password",
        description="The new password of the user",
    )


class TokenPayload(SQLModel):
    sub: int | None = Field(default=None)
    refresh: bool | None = Field(default=None)


class Token(SQLModel):
    access_token: str
    token_type: str = Field(default="bearer")


class WechatToken(Token):
    refresh_token: str
