from collections.abc import Generator
from sqlmodel import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException, status
from pydantic import ValidationError
from jose import JWTError, jwt
from app.core.connections.sql import sqlalchemy_engine
from app.core.config import config
from app.models.user import User
from app.models.security import TokenPayload
from typing import Annotated

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{config.api_prefix}/session/oauth2/token"
)


async def get_session() -> Generator[Session, None, None]:
    with Session(sqlalchemy_engine) as session:
        yield session


TokenDep = Annotated[str, Depends(oauth2_scheme)]
SessionDep = Annotated[Session, Depends(get_session)]
LoginDep = Annotated[OAuth2PasswordRequestForm, Depends()]


async def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, config.jwt_secret, algorithms=[config.jwt_algorithm]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials: Invalid token",
        )
    if token_data.refresh:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not validate credentials: Access token required",
        )
    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials: User not found",
        )
    return user


UserDep = Annotated[User, Depends(get_current_user)]


async def check_admin(user: UserDep) -> User:
    if user.permission < 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return user


AdminDep = Annotated[User, Depends(check_admin)]


async def get_refresh_token(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, config.jwt_secret, algorithms=[config.jwt_algorithm]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials: Invalid token",
        )
    if not token_data.refresh:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not validate credentials: Refresh token required",
        )
    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials: User not found",
        )
    return user


RefreshDep = Annotated[User, Depends(get_refresh_token)]
