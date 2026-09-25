from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DatabaseSettings


class Base(DeclarativeBase):
    pass


def create_database(settings: DatabaseSettings):
    engine = create_engine(
        settings.sqlalchemy_url(), pool_pre_ping=True, connect_args={"connect_timeout": 3}
    )
    return engine, sessionmaker(bind=engine, expire_on_commit=False)
