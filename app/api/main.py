from fastapi import APIRouter
from .routes import users, session, chats, presets, codes, tasks, utils
from app.core.config import config

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(session.router, prefix="/session", tags=["session"])
api_router.include_router(chats.router, prefix="/chats", tags=["chats"])
api_router.include_router(presets.router, prefix="/presets", tags=["presets"])
api_router.include_router(codes.router, prefix="/codes", tags=["code"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

if config.debug:
    api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
