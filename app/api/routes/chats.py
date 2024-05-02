from fastapi import APIRouter, HTTPException, status
from app.models.chat import Chat, ChatCreate, ChatRead, ChatVisibility
from app.models.preset import Preset
from app.models.server import ServerMessage
from app.models.order import OrderBy, Order
from app.api.deps import SessionDep, UserDep
from app.api.resps import ExceptionResponse
from app.core.managers.message import MessageStorage
from sqlmodel import select, asc, desc
from datetime import datetime

router = APIRouter()


@router.get(
    "",
    response_model=list[ChatRead],
    responses=ExceptionResponse.get_responses(401, 403),
)
async def list_chats(
    session: SessionDep,
    user: UserDep,
    offset: int = 0,
    limit: int = 10,
    order_by: OrderBy = OrderBy.CREATE_TIME,
    order: Order = Order.DESC,
):
    order_expr = (
        asc(getattr(Chat, order_by.value))
        if order == Order.ASC
        else desc(getattr(Chat, order_by.value))
    )

    chats = session.exec(
        select(Chat)
        .where(Chat.owner_id == user.id)
        .order_by(order_expr)
        .offset(offset)
        .limit(limit)
    )

    return [
        {
            **chat.model_dump(),
            "messages": MessageStorage.get_messages(chat.id),
        }
        for chat in chats.all()
    ]


@router.post(
    "",
    response_model=ChatRead,
    responses=ExceptionResponse.get_responses(400, 401, 403),
)
async def create_chat(session: SessionDep, user: UserDep, chat: ChatCreate):
    if session.get(Preset, chat.preset_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Preset not found"
        )
    db_chat = Chat(**chat.model_dump(), owner_id=user.id)
    session.add(db_chat)
    session.commit()
    session.refresh(db_chat)
    MessageStorage.set_messages(db_chat.id, chat.messages)
    return {
        **db_chat.model_dump(),
        "messages": MessageStorage.get_messages(db_chat.id),
    }


@router.get(
    "/{chat_id}",
    response_model=ChatRead,
    responses=ExceptionResponse.get_responses(401, 403, 404),
)
async def read_chat(chat_id: str, session: SessionDep, user: UserDep):
    chat = session.get(Chat, chat_id)
    if chat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
        )
    if chat.owner_id != user.id:
        if chat.visibility == ChatVisibility.private:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions: You do not have access to this chat",
            )
        new_chat = Chat(
            **chat.model_dump(include={"preset_id", "title"}), owner_id=user.id
        )
        session.add(new_chat)
        session.commit()
        session.refresh(new_chat)
        MessageStorage.copy_messages(chat_id, new_chat.id)
        return {
            **new_chat.model_dump(),
            "messages": MessageStorage.get_messages(new_chat.id),
        }
    return {
        **chat.model_dump(),
        "messages": MessageStorage.get_messages(chat.id),
    }


@router.put(
    "/{chat_id}",
    response_model=ChatRead,
    responses=ExceptionResponse.get_responses(400, 401, 403, 404),
)
async def update_chat(
    chat_id: str, chat: ChatCreate, session: SessionDep, user: UserDep
):
    if session.get(Preset, chat.preset_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Preset not found"
        )
    db_chat = session.get(Chat, chat_id)
    if db_chat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
        )
    if db_chat.owner_id != user.id and user.permission < 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: You cannot update other user's chat",
        )
    db_chat.sqlmodel_update(chat.model_dump(exclude_unset=True))
    db_chat.update_time = datetime.now()
    session.add(db_chat)
    session.commit()
    session.refresh(db_chat)
    MessageStorage.set_messages(db_chat.id, chat.messages)
    return {
        **db_chat.model_dump(),
        "messages": MessageStorage.get_messages(db_chat.id),
    }


@router.delete(
    "/{chat_id}",
    response_model=ServerMessage,
    responses=ExceptionResponse.get_responses(401, 403, 404),
)
async def delete_chat(chat_id: str, session: SessionDep, user: UserDep):
    chat = session.get(Chat, chat_id)
    if chat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
        )
    if chat.owner_id != user.id and user.permission < 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: You cannot delete other user's chat",
        )
    session.delete(chat)
    session.commit()
    MessageStorage.delete_messages(chat_id)
    return {"message": "Chat deleted successfully"}
