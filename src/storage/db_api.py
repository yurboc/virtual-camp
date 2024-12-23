import logging
from typing import Optional
from aiogram.types import TelegramObject, Message
from storage.db_schema import TgUpdate, TgMessage, TgUser, TgNotification, TgTask
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class Database:
    # Init class with session
    def __init__(self, session: AsyncSession):
        self.session = session

    # Store event
    async def event_to_log(self, event: TelegramObject) -> None:
        record = TgUpdate(
            tg_update=event.model_dump_json(
                exclude_unset=True, exclude_none=True, exclude_defaults=True
            )
        )
        self.session.add(record)
        await self.session.commit()

    # Store message
    async def message_to_log(self, message: Message) -> None:
        record = TgMessage()
        if message and message.from_user and message.from_user.id:
            record.tg_id = message.from_user.id
        if message and message.from_user and message.from_user.full_name:
            record.tg_name = message.from_user.full_name
        if message and message.text:
            record.tg_message = message.text
        self.session.add(record)
        await self.session.commit()

    # Add user
    async def user_add(self, tg_user: TelegramObject) -> None:
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

    # Get user by id
    async def user_by_id(self, user_id: int) -> Optional[TgUser]:
        users = await self.session.execute(select(TgUser).where(TgUser.id == user_id))
        user = users.scalar()
        return user

    # Get user by tg_id
    async def user_by_tg_id(self, tg_id: int) -> Optional[TgUser]:
        users = await self.session.execute(select(TgUser).where(TgUser.tg_id == tg_id))
        user = users.scalar()
        return user

    # Fill registration data
    async def user_reg(self, tg_id, phone, first_name, last_name, username) -> None:
        existing_user = await self.user_by_tg_id(tg_id)
        if not existing_user:
            logger.error(f"Call reg_user() for unknown user {tg_id}")
            return
        existing_user.tg_first_name = first_name
        existing_user.tg_last_name = last_name
        existing_user.tg_phone = phone
        existing_user.name = username
        existing_user.status = "registered"
        await self.user_update(existing_user)

    # Update existing user
    async def user_update(self, user: TgUser) -> None:
        existing_users = await self.session.execute(
            select(TgUser).where(TgUser.tg_id == user.tg_id)
        )
        existing_user = existing_users.scalar()
        if not existing_user:
            logger.error(f"Failed user_update() on user {user.tg_id}")
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

    # Get user status
    async def user_status(self, tg_user: TelegramObject) -> str:
        user = await self.user_by_tg_id(tg_user.id)
        status = "unknown"
        if user:
            status = user.status
        else:
            status = "new_user"
            await self.user_add(tg_user=tg_user)
        logger.info(f"User status is {status}")
        return status

    # Create task
    async def task_add(self, task_uuid: str, user: TgUser) -> TgTask:
        task = TgTask(uuid=task_uuid, user=user)
        self.session.add(task)
        await self.session.commit()
        return task

    # Get task creator
    async def task_user(self, task_id: int) -> Optional[TgUser]:
        # stmt = select(TgTask).options(joinedload(TgTask.user)).where(TgTask.id == task_id)
        stmt = select(TgTask).where(TgTask.id == task_id)
        result = await self.session.execute(stmt)
        task = result.scalars().first()
        # user = task.user
        stmt = select(TgUser).where(TgUser.id == task.user_id)
        result = await self.session.execute(stmt)
        user = result.scalars().first()
        return user

    # Store notification
    async def notification_add(self, user: TgUser, message: str) -> None:
        sent_message = TgNotification(user=user, message=message)
        self.session.add(sent_message)
        await self.session.commit()
        logger.info("Notification was stored")
