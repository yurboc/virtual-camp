import logging
import uuid
from typing import Optional, Sequence, Union
from aiogram.types import TelegramObject, User, Message
from storage.db_schema import TgUpdate, TgMessage, TgUser, TgNotification, TgTask
from storage.db_schema import TgAbonement, TgAbonementUser, TgAbonementPass
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
    async def user_add(self, tg_user: User) -> TgUser:
        users = await self.session.execute(
            select(TgUser).where(TgUser.tg_id == tg_user.id)
        )
        user = users.scalar()
        if not user:
            logger.info(f"Create user {tg_user.id}")
            user = TgUser(
                tg_id=tg_user.id,
                tg_first_name=tg_user.first_name,
                tg_last_name=tg_user.last_name,
                tg_username=tg_user.username,
                name=tg_user.full_name,
                status="unregistered",
            )
            self.session.add(user)
            await self.session.commit()
        return user

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

    # Get user status
    async def get_or_create_user(
        self, tg_user: Union[TelegramObject, User]
    ) -> Optional[TgUser]:
        user = await self.user_by_tg_id(tg_user.id) if type(tg_user) == User else None
        status = "unknown"
        if user:
            status = user.status
        else:
            status = "new_user"
            user = (
                await self.user_add(tg_user=tg_user) if type(tg_user) == User else None
            )
        logger.info(f"User status is {status}")
        return user

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
        if not task:
            return None
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

    # Abonements list for owner
    async def abonements_list_by_owner(self, user: TgUser) -> Sequence[TgAbonement]:
        stmt = select(TgAbonement).where(TgAbonement.owner_id == user.id)
        result = await self.session.execute(stmt)
        abonements = result.scalars().all()
        return abonements

    # Abonements list for user
    async def abonements_list_by_user(self, user: TgUser) -> Sequence[TgAbonement]:
        stmt = (
            select(TgAbonement)
            .join(TgAbonementUser)
            .where(TgAbonementUser.user_id == user.id)
        )
        result = await self.session.execute(stmt)
        abonements = result.scalars().all()
        return abonements

    # Abonement create
    async def abonement_create(
        self,
        name: str,
        owner: TgUser,
        total_passes: int = 0,
        description: Optional[str] = None,
    ) -> TgAbonement:
        abonement_uuid = str(uuid.uuid4())
        abonement = TgAbonement(
            name=name,
            token=abonement_uuid,
            total_passes=total_passes,
            description=description,
            owner=owner,
        )
        self.session.add(abonement)
        await self.session.commit()
        return abonement

    # Abonement by token
    async def abonement_by_token(self, token: str) -> Optional[TgAbonement]:
        stmt = select(TgAbonement).where(TgAbonement.token == token)
        result = await self.session.execute(stmt)
        abonement = result.scalars().first()
        return abonement

    # Abonement by id
    async def abonement_by_id(self, id: int) -> Optional[TgAbonement]:
        stmt = select(TgAbonement).where(TgAbonement.id == id)
        result = await self.session.execute(stmt)
        abonement = result.scalars().first()
        return abonement

    # Abonement add user
    async def abonement_user_add(
        self, user_id: int, abonement_id: int, abonement_token: str
    ) -> Optional[TgAbonementUser]:
        user = await self.user_by_id(user_id)
        abonement = await self.abonement_by_id(abonement_id)
        if not user or not abonement or abonement.token != abonement_token:
            return None
        abonement_user = TgAbonementUser(
            abonement=abonement, user=user, permission="user"
        )
        self.session.add(abonement_user)
        await self.session.commit()
        return abonement_user

    # Abonement user
    async def abonement_user(
        self, user_id: int, abonement_id: int
    ) -> Optional[TgAbonementUser]:
        stmt = select(TgAbonementUser).where(
            TgAbonementUser.user_id == user_id,
            TgAbonementUser.abonement_id == abonement_id,
        )
        result = await self.session.execute(stmt)
        abonement_user = result.scalars().first()
        return abonement_user

    # Abonement pass list
    async def abonement_pass_list(
        self, abonement_id: int, user_id: Optional[int] = None
    ) -> Sequence[TgAbonementPass]:
        if not user_id:
            stmt = select(TgAbonementPass).where(
                TgAbonementPass.abonement_id == abonement_id
            )
        else:
            stmt = select(TgAbonementPass).where(
                TgAbonementPass.abonement_id == abonement_id,
                TgAbonementPass.user_id == user_id,
            )
        result = await self.session.execute(stmt)
        abonement_passes = result.scalars().all()
        return abonement_passes

    # Abonement pass left
    async def abonement_pass_left(self, abonement_id: int) -> Optional[int]:
        abonement = await self.abonement_by_id(abonement_id)
        total_passes = abonement.total_passes if abonement else None
        if not total_passes:
            return None
        stmt = select(TgAbonementPass).where(
            TgAbonementPass.abonement_id == abonement_id
        )
        result = await self.session.execute(stmt)
        abonement_passes = result.scalars().all()
        passes_count = len(abonement_passes)
        return total_passes - passes_count

    # Abonement pass add
    async def abonement_pass_add(
        self, abonement_id: int, user_id: int
    ) -> Optional[TgAbonementPass]:
        pass_left = await self.abonement_pass_left(abonement_id)
        if pass_left is not None and pass_left <= 0:
            return None
        abonement_pass = TgAbonementPass(abonement_id=abonement_id, user_id=user_id)
        self.session.add(abonement_pass)
        await self.session.commit()
        return abonement_pass
