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
    status: Mapped[str]
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
    invites: Mapped[List["TgInviteUser"]] = relationship(
        "TgInviteUser", back_populates="user"
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
    abonement_visits: Mapped[List["TgAbonementVisit"]] = relationship(
        "TgAbonementVisit", back_populates="user"
    )
    settings: Mapped[List["TgSettings"]] = relationship(
        "TgSettings", back_populates="user"
    )

    def __repr__(self) -> str:
        return (
            f"<TgUser(id={self.id}, tg_id={self.tg_id},"
            f" tg_first_name={self.tg_first_name},"
            f" tg_last_name={self.tg_last_name},"
            f" tg_username={self.tg_username}, tg_phone={self.tg_phone},"
            f" name={self.name}, status={self.status},"
            f" create_ts={self.create_ts}, update_ts={self.update_ts})>"
        )


class TgTask(Base):
    __tablename__ = "tg_tasks"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    ts: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.CURRENT_TIMESTAMP(),
    )
    uuid: Mapped[str] = mapped_column(String(60), unique=True)
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
    spreadsheet_id: Mapped[Optional[str]]
    name: Mapped[str]
    total_visits: Mapped[int]
    expiry_date: Mapped[Optional[datetime.datetime]]
    description: Mapped[Optional[str]]
    hidden: Mapped[bool]
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
    visits: Mapped[List["TgAbonementVisit"]] = relationship(
        "TgAbonementVisit", back_populates="abonement"
    )


class TgAbonementUser(Base):
    __tablename__ = "tg_abonement_users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    user: Mapped[TgUser] = relationship("TgUser", back_populates="abonement_uses")
    user_id: Mapped[int] = mapped_column(ForeignKey("tg_users.id"))
    abonement: Mapped[TgAbonement] = relationship("TgAbonement", back_populates="users")
    abonement_id: Mapped[int] = mapped_column(ForeignKey("tg_abonements.id"))


class TgAbonementVisit(Base):
    __tablename__ = "tg_abonement_visits"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    ts: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.CURRENT_TIMESTAMP(),
    )
    user: Mapped[TgUser] = relationship("TgUser", back_populates="abonement_visits")
    user_id: Mapped[int] = mapped_column(ForeignKey("tg_users.id"))
    abonement: Mapped[TgAbonement] = relationship(
        "TgAbonement", back_populates="visits"
    )
    abonement_id: Mapped[int] = mapped_column(ForeignKey("tg_abonements.id"))


class TgInvite(Base):
    __tablename__ = "tg_invites"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    token: Mapped[str] = mapped_column(String(60), index=True, unique=True)
    group: Mapped[str]
    max_uses: Mapped[int]
    max_days: Mapped[int]
    active: Mapped[bool]
    ts_created: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.CURRENT_TIMESTAMP(),
    )
    ts_updated: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.CURRENT_TIMESTAMP(),
        onupdate=func.CURRENT_TIMESTAMP(),
    )
    users: Mapped[List["TgInviteUser"]] = relationship(
        "TgInviteUser", back_populates="invite"
    )


class TgInviteUser(Base):
    __tablename__ = "tg_invite_users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    user: Mapped[TgUser] = relationship("TgUser", back_populates="invites")
    user_id: Mapped[int] = mapped_column(ForeignKey("tg_users.id"))
    invite: Mapped[TgInvite] = relationship("TgInvite", back_populates="users")
    invite_id: Mapped[int] = mapped_column(ForeignKey("tg_invites.id"))
    ts: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.CURRENT_TIMESTAMP(),
    )


class TgSettings(Base):
    __tablename__ = "tg_settings"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    key: Mapped[str] = mapped_column(String(60))
    value: Mapped[str] = mapped_column(String(60))
    user: Mapped[TgUser] = relationship("TgUser", back_populates="settings")
    user_id: Mapped[int] = mapped_column(ForeignKey("tg_users.id"))
