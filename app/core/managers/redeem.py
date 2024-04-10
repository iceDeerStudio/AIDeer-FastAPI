from app.core.connections.redis import redis_client
from app.core.managers.credit import CreditManager
from fastapi import HTTPException


class RedeemCodeNotFound(HTTPException):
    def __init__(self, code: str):
        self.code = code
        super().__init__(status_code=422, detail=f"Invalid redeem code: {code}")


class RedeemManager:

    @staticmethod
    def check_redeem_code(code: str) -> int:
        code = code.upper()
        value = redis_client.hget("redeem_codes", code)
        if value is None:
            raise RedeemCodeNotFound(code)
        return int(value)

    @staticmethod
    def redeem_credit(user_id: int, code: str) -> int:
        code = code.upper()
        value = RedeemManager.check_redeem_code(code)
        RedeemManager.delete_redeem_code(code)
        CreditManager.add_credit(user_id, value, f"Redeem credit, code: {code}")
        return value

    @staticmethod
    def add_redeem_code(code: str, value: int):
        code = code.upper()
        redis_client.hset("redeem_codes", code, value)
        return value

    @staticmethod
    def delete_redeem_code(code: str):
        code = code.upper()
        redis_client.hdel("redeem_codes", code)
        return code
