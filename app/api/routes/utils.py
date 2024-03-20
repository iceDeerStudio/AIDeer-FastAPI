from fastapi import APIRouter, HTTPException, status
from app.api.deps import SessionDep
from app.api.resps import ExceptionResponse
from app.core.connections.sql import sqlalchemy_engine, init_db
from app.core.config import config
from app.core.security import get_password_hash
from app.models.user import User, UserRead
from app.models.server import ServerMessage
from sqlmodel import SQLModel

router = APIRouter()


@router.get("/init", response_model=ServerMessage)
async def init():
    init_db()
    return {"message": "Database initialized"}


@router.get(
    "/admin",
    response_model=UserRead,
    responses=ExceptionResponse.get_responses(500),
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
