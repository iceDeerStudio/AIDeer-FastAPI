from fastapi import APIRouter, HTTPException, status
from app.api.deps import SessionDep
from app.core.connections.sql import sqlalchemy_engine
from app.core.config import config
from app.core.security import get_password_hash
from sqlmodel import SQLModel

from app.models.user import *
from app.models.server import *
from app.models.security import *
from app.models.chat import *
from app.models.preset import *
from app.models.message import *
from app.models.credit import *
from app.models.dashscope import *
from app.models.task import *

router = APIRouter()


@router.get("/init")
async def init():
    SQLModel.metadata.create_all(sqlalchemy_engine)
    return {"message": "Database initialized"}


@router.get(
    "/admin",
    response_model=UserRead,
    responses={
        500: {"description": "Admin credentials not set", "model": ExceptionDetail}
    },
)
async def create_admin(session: SessionDep):
    if config.admin_user and config.admin_passwd:
        password_hash = get_password_hash(config.admin_passwd)
        admin = User(
            username=config.admin_user,
            password_hash=password_hash,
            permission=2,
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)
        return admin
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Admin credentials not set",
    )


@router.get("/drop")
async def drop():
    SQLModel.metadata.drop_all(sqlalchemy_engine)
    return {"message": "Database dropped"}
