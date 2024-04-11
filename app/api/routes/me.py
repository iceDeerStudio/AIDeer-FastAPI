from fastapi import APIRouter, HTTPException, status, UploadFile
from fastapi.responses import RedirectResponse
from app.models.user import User, UserRead
from app.models.security import PasswordUpdate
from app.models.server import ServerMessage
from app.models.like import PresetLikeRecord, ChatLikeRecord, LikesRead
from app.models.preset import Preset
from app.models.chat import Chat
from app.api.deps import UserDep, SessionDep
from app.api.resps import ExceptionResponse
from app.core.security import get_password_hash, verify_password
from app.core.managers.static import StaticFilesManager
from app.core.managers.redeem import RedeemManager
from app.models.credit import CreditRecords, RedeemCredit
from app.core.config import config
from sqlmodel import select

router = APIRouter()


@router.get("", response_model=UserRead, responses=ExceptionResponse.get_responses(401))
async def read_user_me(user: UserDep):
    return user


@router.put(
    "/password",
    response_model=ServerMessage,
    responses=ExceptionResponse.get_responses(400, 401, 404),
)
async def reset_password(user: UserDep, session: SessionDep, password: PasswordUpdate):
    db_user = session.get(User, user.id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if db_user.password_hash is not None:
        if password.old_password is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Old password is required",
            )
        if not verify_password(password.old_password, db_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Old password is incorrect",
            )
    db_user.password_hash = get_password_hash(password.new_password)
    session.add(db_user)
    session.commit()
    return {"message": "Password updated successfully"}


@router.get(
    "/avatar",
    response_class=RedirectResponse,
    responses=ExceptionResponse.get_responses(401),
)
async def get_avatar(user: UserDep):
    return RedirectResponse(f"{config.api_base_url}{user.avatar}")


@router.post(
    "/avatar",
    response_model=ServerMessage,
    responses=ExceptionResponse.get_responses(401, 404),
)
async def set_avatar(user: UserDep, session: SessionDep, avatar_file: UploadFile):
    db_user = session.get(User, user.id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    db_user.avatar = StaticFilesManager.save_avatar_file(await avatar_file.read())
    session.add(db_user)
    session.commit()
    return {"message": "Avatar updated successfully"}


@router.get(
    "/credits",
    response_model=CreditRecords,
    responses=ExceptionResponse.get_responses(401),
)
async def get_credits(user: UserDep):
    return {"credit_records": user.credit_records, "credits_left": user.credits_left}


@router.post(
    "/credits",
    response_model=ServerMessage,
    responses=ExceptionResponse.get_responses(401, 422),
)
async def redeem_credits(user: UserDep, redeem: RedeemCredit):
    value = RedeemManager.redeem_credit(user.id, redeem.redeem_code)
    return {"message": f"Redeem {value} credits successfully"}


@router.get(
    "/likes",
    response_model=LikesRead,
    responses=ExceptionResponse.get_responses(401),
)
async def read_likes(user: UserDep):
    preset_ids = [like.preset_id for like in user.liked_presets]
    chat_ids = [like.chat_id for like in user.liked_chats]
    return LikesRead(preset_ids=preset_ids, chat_ids=chat_ids)


@router.post(
    "/likes/preset/{preset_id}",
    response_model=PresetLikeRecord,
    responses=ExceptionResponse.get_responses(400, 401, 404),
)
async def create_like_preset(user: UserDep, session: SessionDep, preset_id: str):
    preset = session.get(Preset, preset_id)

    if preset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preset not found",
        )

    like_record = session.exec(
        select(PresetLikeRecord)
        .where(PresetLikeRecord.user_id == user.id)
        .where(PresetLikeRecord.preset_id == preset_id)
    ).first()

    if like_record is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Like already exists",
        )

    like_record = PresetLikeRecord(user_id=user.id, preset_id=preset_id)
    session.add(like_record)
    session.commit()
    session.refresh(like_record)
    return like_record


@router.delete(
    "/likes/preset/{preset_id}",
    response_model=ServerMessage,
    responses=ExceptionResponse.get_responses(401, 404),
)
async def delete_like_preset(user: UserDep, session: SessionDep, preset_id: str):
    like_record = session.exec(
        select(PresetLikeRecord)
        .where(PresetLikeRecord.user_id == user.id)
        .where(PresetLikeRecord.preset_id == preset_id)
    ).first()

    if like_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Like not found",
        )

    session.delete(like_record)
    session.commit()
    return ServerMessage(message="Like deleted successfully")


@router.post(
    "/likes/chat/{chat_id}",
    response_model=ChatLikeRecord,
    responses=ExceptionResponse.get_responses(400, 401, 404),
)
async def create_like_chat(user: UserDep, session: SessionDep, chat_id: str):
    chat = session.get(Chat, chat_id)

    if chat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    like_record = session.exec(
        select(ChatLikeRecord)
        .where(ChatLikeRecord.user_id == user.id)
        .where(ChatLikeRecord.chat_id == chat_id)
    ).first()

    if like_record is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Like already exists",
        )

    like_record = ChatLikeRecord(user_id=user.id, chat_id=chat_id)
    session.add(like_record)
    session.commit()
    session.refresh(like_record)
    return like_record


@router.delete(
    "/likes/chat/{chat_id}",
    response_model=ServerMessage,
    responses=ExceptionResponse.get_responses(401, 404),
)
async def delete_like_chat(user: UserDep, session: SessionDep, chat_id: str):
    like_record = session.exec(
        select(ChatLikeRecord)
        .where(ChatLikeRecord.user_id == user.id)
        .where(ChatLikeRecord.chat_id == chat_id)
    ).first()

    if like_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Like not found",
        )

    session.delete(like_record)
    session.commit()
    return ServerMessage(message="Like deleted successfully")
