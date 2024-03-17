from fastapi import APIRouter, HTTPException, status
from app.models.chat import Chat, ChatCreate, ChatRead, ChatVisibility
from app.models.server import ServerMessage
from app.api.deps import SessionDep, UserDep
from app.core.managers.message import MessageStorage
from sqlmodel import select

router = APIRouter()


@router.get("", response_model=list[ChatRead])
async def list_chats(
    session: SessionDep, user: UserDep, offset: int = 0, limit: int = 10
):
    chats = session.exec(
        select(Chat).where(Chat.owner_id == user.id).offset(offset).limit(limit)
    )
    return [
        {
            **chat.model_dump(),
            "messages": MessageStorage.get_messages(chat.id),
        }
        for chat in chats.all()
    ]


@router.post("", response_model=ChatRead)
async def create_chat(session: SessionDep, user: UserDep, chat: ChatCreate):
    db_chat = Chat(**chat.model_dump(), owner_id=user.id)
    session.add(db_chat)
    session.commit()
    session.refresh(db_chat)
    MessageStorage.set_messages(db_chat.id, chat.messages)
    return {
        **db_chat.model_dump(),
        "messages": MessageStorage.get_messages(db_chat.id),
    }


@router.get("/{chat_id}", response_model=ChatRead)
async def read_chat(chat_id: str, session: SessionDep, user: UserDep):
    chat = session.get(Chat, chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
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


@router.put("/{chat_id}", response_model=ChatRead)
async def update_chat(
    chat_id: str, chat: ChatCreate, session: SessionDep, user: UserDep
):
    db_chat = session.get(Chat, chat_id)
    if db_chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    if db_chat.owner_id != user.id and user.permission < 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: You cannot update other user's chat",
        )
    db_chat.sqlmodel_update(chat.model_dump(exclude_unset=True))
    session.add(db_chat)
    session.commit()
    session.refresh(db_chat)
    MessageStorage.set_messages(db_chat.id, chat.messages)
    return {
        **db_chat.model_dump(),
        "messages": MessageStorage.get_messages(db_chat.id),
    }


@router.delete("/{chat_id}", response_model=ServerMessage)
async def delete_chat(chat_id: str, session: SessionDep, user: UserDep):
    chat = session.get(Chat, chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat.owner_id != user.id and user.permission < 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: You cannot delete other user's chat",
        )
    session.delete(chat)
    session.commit()
    MessageStorage.delete_messages(chat_id)
    return {"message": "Chat deleted successfully"}
