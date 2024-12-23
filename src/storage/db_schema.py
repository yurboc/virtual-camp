import datetime
from typing import List
from typing import Optional
from sqlalchemy import func
from sqlalchemy import ForeignKey
from sqlalchemy import String, BigInteger, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


# Mapping
class Base(DeclarativeBase):
    pass


class TgUpdate(Base):
    __tablename__ = "tg_all_updates"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    ts: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.CURRENT_TIMESTAMP()
    )
    tg_update: Mapped[str]


class TgMessage(Base):
    __tablename__ = "tg_all_messages"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    ts: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.CURRENT_TIMESTAMP()
    )
    tg_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    tg_name: Mapped[Optional[str]] = mapped_column(String(60))
    tg_message: Mapped[Optional[str]]


class TgUser(Base):
    __tablename__ = "tg_users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, unique=True)
    tg_first_name: Mapped[Optional[str]] = mapped_column(String(60))
    tg_last_name: Mapped[Optional[str]] = mapped_column(String(60))
    tg_username: Mapped[Optional[str]] = mapped_column(String(60))
    tg_phone: Mapped[Optional[str]] = mapped_column(String(30))
    name: Mapped[Optional[str]] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(15))
    create_ts: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.CURRENT_TIMESTAMP(),
    )
    update_ts: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.CURRENT_TIMESTAMP(),
        onupdate=func.CURRENT_TIMESTAMP(),
    )
    tasks: Mapped[List["TgTask"]] = relationship("TgTask", back_populates="user")
    notifications: Mapped[List["TgNotification"]] = relationship(
        "TgNotification", back_populates="user"
    )


class TgTask(Base):
    __tablename__ = "tg_tasks"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    ts: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.CURRENT_TIMESTAMP(),
    )
    uuid: Mapped[str]
    user: Mapped[TgUser] = relationship("TgUser", back_populates="tasks")
    user_id: Mapped[int] = mapped_column(ForeignKey("tg_users.id"))


class TgNotification(Base):
    __tablename__ = "tg_notifications"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    ts: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.CURRENT_TIMESTAMP(),
    )
    message: Mapped[str]
    user: Mapped[TgUser] = relationship("TgUser", back_populates="notifications")
    user_id: Mapped[int] = mapped_column(ForeignKey("tg_users.id"))
