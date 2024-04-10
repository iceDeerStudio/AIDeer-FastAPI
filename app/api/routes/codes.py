from app.core.managers.redeem import RedeemManager
from app.api.deps import AdminDep, SessionDep
from app.api.resps import ExceptionResponse
from app.models.credit import RedeemCode
from app.models.server import ServerMessage
from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/{code}", response_model=RedeemCode, responses=ExceptionResponse.get_responses(422)
)
async def read_redeem_code(_user: SessionDep, code: str):
    value = RedeemManager.check_redeem_code(code)
    return {"redeem_code": code, "value": value}


@router.post(
    "", response_model=RedeemCode, responses=ExceptionResponse.get_responses(401, 403)
)
async def create_redeem_code(_admin: AdminDep, redeem_code: RedeemCode):
    RedeemManager.add_redeem_code(redeem_code.redeem_code, redeem_code.value)
    return redeem_code


@router.delete(
    "/{code}",
    response_model=ServerMessage,
    responses=ExceptionResponse.get_responses(401, 403),
)
async def delete_redeem_code(_admin: AdminDep, code: str):
    RedeemManager.delete_redeem_code(code)
    return {"message": f"Redeem code {code} deleted successfully"}
