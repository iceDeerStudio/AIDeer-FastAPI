from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


class CreditRecordBase(SQLModel):
    user_id: int = Field(
        title="User ID", description="User's unique identifier", foreign_key="user.id"
    )
    amount: int = Field(
        title="Credit amount",
        description="The amount of credit",
    )
    description: str = Field(
        title="Credit description",
        description="The description of the credit record",
    )
    create_time: datetime = Field(
        title="Create time",
        description="The time when the credit record is created",
        default_factory=datetime.now,
    )


class CreditRecord(CreditRecordBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user: "User" = Relationship(back_populates="credit_records")


class CreditRecordRead(CreditRecordBase):
    id: int = Field(
        title="Credit record ID", description="Credit record's unique identifier"
    )


class CreditRecords(SQLModel):
    credit_records: List[CreditRecordRead] = Field(
        title="Credit records", description="Credit records of the user"
    )
    credits_left: int = Field(
        title="Credits left",
        description="The amount of credits left",
    )


class RedeemCredit(SQLModel):
    redeem_code: str = Field(
        title="Redeem code",
        description="The redeem code to redeem credits",
    )


class RedeemCode(SQLModel):
    redeem_code: str = Field(
        title="Redeem code",
        description="The redeem code to redeem credits",
    )
    value: int = Field(
        title="Redeem value",
        description="The value of the redeem code",
    )


# Import Models
from .user import User

# Rebuild Models
CreditRecord.model_rebuild()
