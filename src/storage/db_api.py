import logging
from typing import Optional
from aiogram.types import TelegramObject, Message
from storage.db_schema import TgUpdate, TgMessage, TgUser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def store_event(self, event: TelegramObject) -> None:
        record = TgUpdate(
            tg_update=event.model_dump_json(
                exclude_unset=True, exclude_none=True, exclude_defaults=True
            )
        )
        self.session.add(record)
        await self.session.commit()

    async def store_message(self, message: Message) -> None:
        record = TgMessage()
        if message and message.from_user and message.from_user.id:
            record.tg_id = message.from_user.id
        if message and message.from_user and message.from_user.full_name:
            record.tg_name = message.from_user.full_name
        if message and message.text:
            record.tg_message = message.text
        self.session.add(record)
        await self.session.commit()

    async def add_user(self, tg_user: TelegramObject) -> None:
        users = await self.session.execute(
            select(TgUser).where(TgUser.tg_id == tg_user.id)
        )
        user = users.scalar()
        if not user:
            logger.info(f"Create user {tg_user.id}")
            new_user = TgUser(
                tg_id=tg_user.id,
                tg_first_name=tg_user.first_name,
                tg_last_name=tg_user.last_name,
                tg_username=tg_user.username,
                name=tg_user.full_name,
                status="unregistered",
            )
            self.session.add(new_user)
            await self.session.commit()

    async def update_user(self, user: TgUser) -> None:
        existing_users = await self.session.execute(
            select(TgUser).where(TgUser.tg_id == user.tg_id)
        )
        existing_user = existing_users.scalar()
        if not existing_user:
            logger.error(f"Failed update_user() on user {user.tg_id}")
            return
        db_user = await self.session.get(
            TgUser, {"id": existing_user.id, "tg_id": existing_user.tg_id}
        )
        if db_user:
            logger.info(f"Update user {user.tg_id}")
            db_user.tg_first_name = user.tg_first_name
            db_user.tg_last_name = user.tg_last_name
            db_user.tg_phone = user.tg_phone
            db_user.name = user.name
            db_user.status = user.status
            await self.session.commit()

    async def get_user_data(self, tg_id: int) -> Optional[TgUser]:
        users = await self.session.execute(select(TgUser).where(TgUser.tg_id == tg_id))
        user = users.scalar()
        return user

    async def check_user(self, tg_user: TelegramObject) -> str:
        user = await self.get_user_data(tg_user.id)
        status = "unknown"
        if user:
            status = user.status
        else:
            status = "new_user"
            await self.add_user(tg_user=tg_user)
        logger.info(f"User status is {status}")
        return status

    async def reg_user(self, tg_id, phone, first_name, last_name, username) -> None:
        existing_user = await self.get_user_data(tg_id)
        if not existing_user:
            logger.error(f"Call reg_user() for unknown user {tg_id}")
            return
        existing_user.tg_first_name = first_name
        existing_user.tg_last_name = last_name
        existing_user.tg_phone = phone
        existing_user.name = username
        existing_user.status = "registered"
        await self.update_user(existing_user)
