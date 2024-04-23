from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse
from app.models.user import User, UserCreate, UserRead, UserBase
from app.models.security import PasswordUpdate
from app.models.server import ServerMessage
from app.api.deps import SessionDep, UserDep, AdminDep
from app.api.resps import ExceptionResponse
from app.api.routes import me
from app.core.security import get_password_hash
from app.core.config import config
from sqlmodel import select

router = APIRouter()
router.include_router(me.router, prefix="/me")


@router.get(
    "",
    response_model=list[UserRead],
    responses=ExceptionResponse.get_responses(401, 403),
)
async def list_users(
    _admin: AdminDep, session: SessionDep, offset: int = 0, limit: int = 10
):
    users = session.exec(select(User).offset(offset).limit(limit))
    return users.all()


@router.post(
    "", response_model=UserRead, responses=ExceptionResponse.get_responses(400, 403)
)
async def create_user(session: SessionDep, user: UserCreate):
    if user.permission >= 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: Cannot create admin user",
        )
    if session.exec(select(User).where(User.username == user.username)).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )
    password_hash = get_password_hash(user.password)
    db_user = User(**user.model_dump(), password_hash=password_hash)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.get(
    "/{user_id}",
    response_model=UserRead,
    responses=ExceptionResponse.get_responses(401, 404),
)
async def read_user(_user: UserDep, user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.put(
    "/{user_id}",
    response_model=UserRead,
    responses=ExceptionResponse.get_responses(400, 401, 403, 404),
)
async def update_user(
    user_id: int, user: UserBase, session: SessionDep, current_user: UserDep
):
    db_user = session.get(User, user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if db_user.id != current_user.id and current_user.permission != 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: You cannot update other users",
        )
    if user.permission == 2 and current_user.permission != 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: You cannot set user permission to admin",
        )
    if user.username is not None and user.username != db_user.username:
        if session.exec(select(User).where(User.username == user.username)).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )
    db_user.sqlmodel_update(user.model_dump(exclude_unset=True))
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.delete(
    "/{user_id}",
    response_model=ServerMessage,
    responses=ExceptionResponse.get_responses(401, 403, 404),
)
async def delete_user(_admin: AdminDep, user_id: int, session: SessionDep):
    db_user = session.get(User, user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    session.delete(db_user)
    session.commit()
    return {"message": "User deleted successfully"}


@router.put(
    "/{user_id}/password",
    response_model=ServerMessage,
    responses=ExceptionResponse.get_responses(401, 403, 404),
)
async def reset_user_password(
    _admin: AdminDep, user_id: int, session: SessionDep, password: PasswordUpdate
):
    db_user = session.get(User, user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    db_user.password_hash = get_password_hash(password.new_password)
    session.add(db_user)
    session.commit()
    return {"message": "Password updated successfully"}


@router.get(
    "/{user_id}/avatar",
    response_class=RedirectResponse,
    responses=ExceptionResponse.get_responses(401, 404),
)
async def get_user_avatar(_user: UserDep, user_id: int, session: SessionDep):
    db_user = session.get(User, user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return RedirectResponse(f"{config.api_base_url}{db_user.avatar}")
