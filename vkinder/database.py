from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from vkinder.config import get_settings


class Base(DeclarativeBase):
    """класс ORM-моделей."""


settings = get_settings()

engine = create_engine(settings.database_url, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
