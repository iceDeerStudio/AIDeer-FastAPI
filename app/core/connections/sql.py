from sqlmodel import create_engine, SQLModel
from app.core.config import config


sqlalchemy_engine = create_engine(config.database_url)


def init_db():
    from app.models import (
        user,
        server,
        security,
        chat,
        preset,
        message,
        credit,
        dashscope,
        task,
        like,
    )

    SQLModel.metadata.create_all(sqlalchemy_engine)


def drop_db():
    SQLModel.metadata.drop_all(sqlalchemy_engine)
