import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Sequence, Union
from aiogram.types import TelegramObject, User, Message
from storage.db_schema import TgUpdate, TgMessage, TgUser, TgNotification, TgTask
from storage.db_schema import TgAbonement, TgAbonementUser, TgAbonementVisit
from storage.db_schema import TgInvite, TgInviteUser
from sqlalchemy import select, not_
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import func
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

    # Update user
    async def user_update(self, user: TgUser) -> Optional[TgUser]:
        stmt = select(TgUser).where(TgUser.id == user.id)
        result = await self.session.execute(stmt)
        db_user = result.scalars().first()
        if not db_user:
            logger.warning(f"User {user.id} not found in DB")
            return None
        logger.info(f"Update user {user.id}")
        db_user = user
        await self.session.commit()
        return db_user

    # Get user by id
    async def user_by_id(self, user_id: int) -> Optional[TgUser]:
        users = await self.session.execute(select(TgUser).where(TgUser.id == user_id))
        user = users.scalars().first()
        return user

    # Get user by tg_id
    async def user_by_tg_id(self, tg_id: int) -> Optional[TgUser]:
        users = await self.session.execute(select(TgUser).where(TgUser.tg_id == tg_id))
        user = users.scalars().first()
        return user

    # Get user status
    async def user_get_or_create(
        self, tg_user: Union[TelegramObject, User]
    ) -> Optional[TgUser]:
        user = (
            await self.user_by_tg_id(tg_user.id) if isinstance(tg_user, User) else None
        )
        user_status = ["unknown"]
        if user:
            user_status = self.user_get_groups(user)
        else:
            user_status = ["new_user"]
            user = (
                await self.user_add(tg_user=tg_user)
                if isinstance(tg_user, User)
                else None
            )
        logger.info(f"User status is {user_status}")
        return user

    # Get user groups
    def user_get_groups(self, user: TgUser) -> list[str]:
        groups = user.status.split()
        return groups

    # User add to group
    def user_add_to_group(self, user: TgUser, group: str) -> None:
        groups = self.user_get_groups(user)
        groups.append(group)
        if "registered" in groups and group == "unregistered":
            groups.remove("registered")
        elif "unregistered" in groups and group == "registered":
            groups.remove("unregistered")
        user.status = " ".join(groups)

    # Create task
    async def task_add(self, task_uuid: str, user: TgUser) -> TgTask:
        task = TgTask(uuid=task_uuid, user=user)
        self.session.add(task)
        await self.session.commit()
        return task

    # Get task creator
    async def task_user(self, task_id: int) -> Optional[TgUser]:
        stmt_task = select(TgTask).where(TgTask.id == task_id)
        result_task = await self.session.execute(stmt_task)
        task = result_task.scalars().first()
        if not task:
            return None
        stmt_user = select(TgUser).where(TgUser.id == task.user_id)
        result_user = await self.session.execute(stmt_user)
        user = result_user.scalars().first()
        return user

    # Store notification
    async def notification_add(self, user: TgUser, message: str) -> None:
        sent_message = TgNotification(user=user, message=message)
        self.session.add(sent_message)
        await self.session.commit()
        logger.info("Notification was stored")

    # Abonements list for owner
    async def abonements_list_by_owner(self, user: TgUser) -> Sequence[TgAbonement]:
        stmt = select(TgAbonement).where(
            TgAbonement.owner_id == user.id, not_(TgAbonement.hidden)
        )
        result = await self.session.execute(stmt)
        abonements = result.scalars().all()
        return abonements

    # Abonements list for user
    async def abonements_list_by_user(self, user: TgUser) -> Sequence[TgAbonement]:
        stmt = (
            select(TgAbonement)
            .join(TgAbonementUser)
            .where(TgAbonementUser.user_id == user.id, not_(TgAbonement.hidden))
        )
        result = await self.session.execute(stmt)
        abonements = result.scalars().all()
        return abonements

    # Abonement create
    async def abonement_create(
        self,
        name: str,
        owner: TgUser,
        total_visits: int = 0,
        description: Optional[str] = None,
    ) -> TgAbonement:
        abonement_uuid = str(uuid.uuid4())
        abonement = TgAbonement(
            name=name,
            token=abonement_uuid,
            total_visits=total_visits,
            description=description,
            owner=owner,
        )
        self.session.add(abonement)
        await self.session.commit()
        return abonement

    # Abonement edit
    async def abonement_edit(
        self,
        abonement_id: int,
        name: str,
        owner: TgUser,
        total_visits: int = 0,
        description: Optional[str] = None,
    ) -> Optional[TgAbonement]:
        abonement = await self.abonement_by_id(abonement_id)
        if not abonement or abonement.owner_id != owner.id:
            return None
        abonement.name = name
        abonement.total_visits = total_visits
        abonement.description = description
        await self.session.commit()
        return abonement

    # Abonement delete
    async def abonement_delete(self, abonement_id: int, user_id: int) -> bool:
        abonement = await self.abonement_by_id(abonement_id)
        # Check abonement
        if not abonement:
            return False
        # For user: "unlink" abonement
        if abonement.owner_id != user_id:
            abonement_user = await self.abonement_user(user_id, abonement_id)
            if not abonement_user:
                return False
            await self.session.delete(abonement_user)
        # For owner: "delete" abonement
        else:
            abonement.hidden = True  # not "await self.session.delete(abonement)"
        # Save changes
        await self.session.commit()
        return True

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
        abonement_user = TgAbonementUser(abonement=abonement, user=user)
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

    # Abonement visit count
    async def abonement_visits_count(
        self, abonement_id: int, user_id: Optional[int] = None
    ) -> int:
        if not user_id:
            stmt = (
                func.count()
                .select()
                .where(TgAbonementVisit.abonement_id == abonement_id)
            )
        else:
            stmt = (
                func.count()
                .select()
                .where(
                    TgAbonementVisit.abonement_id == abonement_id,
                    TgAbonementVisit.user_id == user_id,
                )
            )
        result = await self.session.execute(stmt)
        abonement_visits = result.scalar() or 0
        return abonement_visits

    # Abonement visit list
    async def abonement_visits_list(
        self, abonement_id: int, limit: int, offset: int
    ) -> Sequence[TgAbonementVisit]:
        stmt = (
            select(TgAbonementVisit)
            .options(joinedload(TgAbonementVisit.user))
            .where(TgAbonementVisit.abonement_id == abonement_id)
            .order_by(TgAbonementVisit.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        abonement_visits = result.scalars().all()
        return abonement_visits

    # Abonement visits left
    async def abonement_visits_left(self, abonement: TgAbonement) -> Optional[int]:
        total_visits = abonement.total_visits
        if not total_visits:
            return None
        stmt = (
            func.count().select().where(TgAbonementVisit.abonement_id == abonement.id)
        )
        result = await self.session.execute(stmt)
        visits_count = result.scalar() or 0
        return total_visits - visits_count

    # Abonement visit add
    async def abonement_visit_add(
        self, abonement_id: int, user_id: int
    ) -> Optional[TgAbonementVisit]:
        abonement = await self.abonement_by_id(abonement_id)
        if not abonement or abonement.hidden:
            return None
        visits_left = await self.abonement_visits_left(abonement)
        if visits_left is not None and visits_left <= 0:
            return None
        abonement_visit = TgAbonementVisit(abonement_id=abonement_id, user_id=user_id)
        self.session.add(abonement_visit)
        await self.session.commit()
        return abonement_visit

    # Create invite
    async def invite_create(self, token: str, group: str) -> TgInvite:
        invite = TgInvite(token=token, group=group, max_uses=0, max_days=0, active=True)
        self.session.add(invite)
        await self.session.commit()
        return invite

    # Invite list
    async def invite_list(self) -> Sequence[TgInvite]:
        stmt = select(TgInvite)
        result = await self.session.execute(stmt)
        invites = result.scalars().all()
        return invites

    # Invite users
    async def invite_users(self, invite: TgInvite) -> Sequence[TgInviteUser]:
        stmt = select(TgInviteUser).where(TgInviteUser.invite_id == invite.id)
        result = await self.session.execute(stmt)
        invite_users = result.scalars().all()
        return invite_users

    # Get invite
    async def invite_by_token(self, token: str) -> Optional[TgInvite]:
        stmt = select(TgInvite).where(TgInvite.token == token)
        result = await self.session.execute(stmt)
        invite = result.scalars().first()
        return invite

    # Accept invite
    async def invite_accept(self, user_id: int, invite: TgInvite) -> bool:
        # Get user
        user = await self.user_by_id(user_id)
        if not user:
            return False
        # Check max uses
        stmt = func.count().select().where(TgInviteUser.id == user.id)
        result = await self.session.execute(stmt)
        accepted_invites = result.scalars().all()
        if invite.max_uses and len(accepted_invites) >= invite.max_uses:
            return False
        # Check max days
        if invite.max_days and datetime.now() > invite.ts_created + timedelta(
            days=invite.max_days
        ):
            return False
        # Accept invite by user
        self.user_add_to_group(user, invite.group)
        # Accept invite
        invite_user = TgInviteUser(user_id=user_id, invite_id=invite.id)
        self.session.add(invite_user)
        # Save changes
        await self.session.commit()
        return True
