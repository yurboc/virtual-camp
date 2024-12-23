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
        user = data.get("event_from_user")
        if db and user and user.id:
            user_type = await db.user_status(tg_user=user)
            data["user_type"] = list(user_type.split())
            data["user_id"] = user.id
            logger.info(f"CheckUserType for user {user.id} is {data['user_type']}")
        result = await handler(event, data)
        logger.info("End CheckUserType")
        return result
