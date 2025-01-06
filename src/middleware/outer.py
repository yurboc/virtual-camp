import logging
from typing import Any, Awaitable, Callable, Dict
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from storage.db_api import Database

logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, session: async_sessionmaker[AsyncSession]) -> None:
        self.session = session

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        logger.info("Begin DatabaseMiddleware")
        async with self.session() as session:
            db = Database(session=session)
            data["db"] = db
            result = await handler(event, data)
            logger.info("End DatabaseMiddleware")
            return result


class StoreAllUpdates(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        logger.info("Begin StoreAllUpdates")
        db: Database | None = data.get("db")
        if db:
            await db.event_to_log(event)
        result = await handler(event, data)
        logger.info("End StoreAllUpdates")
        return result


class CheckUserType(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        logger.info("Begin CheckUserType")
        db: Database | None = data.get("db")
        tg_user = data.get("event_from_user")  # stored by built-in aiogram middleware
        if db and tg_user and tg_user.id:
            user = await db.get_or_create_user(tg_user=tg_user)
            if not user:
                logger.warning(f"User {tg_user.id} not found in DB")
            else:
                data["user_type"] = list(user.status.split())
                data["user_tg_id"] = user.tg_id
                data["user_id"] = user.id
                logger.info(f"User {user.tg_id} ({user.id}) is {data['user_type']}")
        result = await handler(event, data)
        logger.info("End CheckUserType")
        return result
