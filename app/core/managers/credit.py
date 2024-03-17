from sqlmodel import Session
from app.models.credit import CreditRecord
from app.models.user import User
from app.core.connections.sql import sqlalchemy_engine
from fastapi import HTTPException


class CreditNotEnough(HTTPException):
    def __init__(self, user: User, amount: int):
        self.user = user
        self.amount = amount
        super().__init__(
            status_code=402,
            detail=f"User {user.username} has only {user.credits_left} credits left, not enough for {amount}",
        )


class CreditManager:
    @staticmethod
    def check_credit(user_id: int, amount: int) -> None:
        with Session(sqlalchemy_engine) as session:
            user = session.get(User, user_id)
        if user.credits_left < amount:
            raise CreditNotEnough(user, amount)
        return None

    @staticmethod
    def consume_credit(user_id: int, amount: int, description: str) -> None:
        with Session(sqlalchemy_engine) as session:
            user = session.get(User, user_id)
            user.credits_left -= amount
            credit = CreditRecord(
                user_id=user.id, amount=-amount, description=f"Consume: {description}"
            )
            session.add(credit)
            session.commit()
        return None

    @staticmethod
    def add_credit(user_id: int, amount: int, description: str) -> None:
        with Session(sqlalchemy_engine) as session:
            user = session.get(User, user_id)
            user.credits_left += amount
            credit = CreditRecord(
                user_id=user.id, amount=amount, description=f"Add: {description}"
            )
            session.add(credit)
            session.commit()
        return None
