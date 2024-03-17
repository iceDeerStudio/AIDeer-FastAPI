from sqlmodel import create_engine
from app.core.config import config


sqlalchemy_engine = create_engine(config.database_url)
