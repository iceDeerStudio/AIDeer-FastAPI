from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from app.models.user import User
from app.models.security import Token, WechatToken
from app.core.clients.wechat import wechat_client_async
from app.core.security import verify_password, create_token
from app.core.config import config
from app.api.deps import SessionDep, LoginDep, RefreshDep
from app.api.resps import ExceptionResponse
from datetime import timedelta
import random

router = APIRouter()


@router.post(
    "/oauth2/token",
    response_model=Token,
    responses=ExceptionResponse.get_responses(401),
)
async def login_for_access_token(session: SessionDep, login_credentials: LoginDep):
    user = session.exec(
        select(User).where(User.username == login_credentials.username)
    ).one_or_none()
    if not user or not verify_password(login_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token_expires = timedelta(minutes=config.jwt_access_token_expires)
    access_token = create_token(subject=user.id, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get(
    "/wechat/token",
    response_model=WechatToken,
    responses=ExceptionResponse.get_responses(401, 500),
)
async def wechat_login_for_tokens(session: SessionDep, code: str):
    openid, session_key = await wechat_client_async.wechat_login(code)
    user = session.exec(select(User).where(User.openid == openid)).one_or_none()
    if not user:
        while True:
            username = "wechat_" + str(random.randint(10000000, 99999999))
            if not session.exec(
                select(User).where(User.username == username)
            ).one_or_none():
                break
        user = User(
            username=username,
            wechat_openid=openid,
            wechat_session_key=session_key,
            permission=1,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    access_token_expires = timedelta(minutes=config.jwt_access_token_expires)
    access_token = create_token(subject=user.id, expires_delta=access_token_expires)
    refresh_token_expires = timedelta(minutes=config.jwt_refresh_token_expires)
    refresh_token = create_token(
        subject=user.id, expires_delta=refresh_token_expires, refresh=True
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get(
    "/wechat/refresh",
    response_model=WechatToken,
    responses=ExceptionResponse.get_responses(401, 500),
)
async def wechat_refresh_for_access_token(user: RefreshDep):
    if not await wechat_client_async.check_wechat_session(
        user.wechat_openid, user.wechat_session_key
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Wechat session expired"
        )
    access_token_expires = timedelta(minutes=config.jwt_access_token_expires)
    access_token = create_token(subject=user.id, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}
