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
    tg_id: Mapped[int] = mapped_column(BigInteger, index=True, unique=True)
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
    abonements: Mapped[List["TgAbonement"]] = relationship(
        "TgAbonement", back_populates="owner"
    )
    abonement_uses: Mapped[List["TgAbonementUser"]] = relationship(
        "TgAbonementUser", back_populates="user"
    )
    abonement_passes: Mapped[List["TgAbonementPass"]] = relationship(
        "TgAbonementPass", back_populates="user"
    )

    def __repr__(self) -> str:
        return (
            f"<TgUser(id={self.id}, tg_id={self.tg_id},"
            f" tg_first_name={self.tg_first_name}, tg_last_name={self.tg_last_name},"
            f" tg_username={self.tg_username}, tg_phone={self.tg_phone}, name={self.name},"
            f" status={self.status}, create_ts={self.create_ts}, update_ts={self.update_ts})>"
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


class TgAbonement(Base):
    __tablename__ = "tg_abonements"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    token: Mapped[str] = mapped_column(String(60), index=True, unique=True)
    name: Mapped[str]
    total_passes: Mapped[int]
    description: Mapped[Optional[str]]
    create_ts: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.CURRENT_TIMESTAMP(),
    )
    owner: Mapped[TgUser] = relationship("TgUser", back_populates="abonements")
    owner_id: Mapped[int] = mapped_column(ForeignKey("tg_users.id"))
    users: Mapped[List["TgAbonementUser"]] = relationship(
        "TgAbonementUser", back_populates="abonement"
    )
    passes: Mapped[List["TgAbonementPass"]] = relationship(
        "TgAbonementPass", back_populates="abonement"
    )


class TgAbonementUser(Base):
    __tablename__ = "tg_abonement_users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    permission: Mapped[str]
    user: Mapped[TgUser] = relationship("TgUser", back_populates="abonement_uses")
    user_id: Mapped[int] = mapped_column(ForeignKey("tg_users.id"))
    abonement: Mapped[TgAbonement] = relationship("TgAbonement", back_populates="users")
    abonement_id: Mapped[int] = mapped_column(ForeignKey("tg_abonements.id"))


class TgAbonementPass(Base):
    __tablename__ = "tg_abonement_passes"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    ts: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.CURRENT_TIMESTAMP(),
    )
    user: Mapped[TgUser] = relationship("TgUser", back_populates="abonement_passes")
    user_id: Mapped[int] = mapped_column(ForeignKey("tg_users.id"))
    abonement: Mapped[TgAbonement] = relationship(
        "TgAbonement", back_populates="passes"
    )
    abonement_id: Mapped[int] = mapped_column(ForeignKey("tg_abonements.id"))
