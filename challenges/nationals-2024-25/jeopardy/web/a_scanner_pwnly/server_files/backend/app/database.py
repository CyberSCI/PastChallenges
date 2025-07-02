import uuid
from collections.abc import AsyncGenerator
from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from sqlalchemy import ForeignKey
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.config import settings


class Base(DeclarativeBase):
    pass


class User(Base, SQLAlchemyBaseUserTableUUID):
    first_name: Mapped[str]
    last_name: Mapped[str]
    national_id: Mapped[str]
    date_of_birth: Mapped[date]

    qr_codes: Mapped[list["QRCode"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class QRCode(Base):
    __tablename__ = "qr_code"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"))
    url: Mapped[str]

    user: Mapped[User] = relationship(back_populates="qr_codes")


engine = create_async_engine(settings.DATABASE_URL.get_secret_value())
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    yield SQLAlchemyUserDatabase(session, User)
