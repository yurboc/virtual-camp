import logging
from typing import Any, Awaitable, Callable, Dict, Optional, Union
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from storage.db_api import Database

logger = logging.getLogger(__name__)


class StoreAllMessages(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, TelegramObject],
        data: Dict[str, Any],
    ) -> Any:
        logger.info("Begin StoreAllMessages")
        db: Optional[Database] = data.get("db")
        if db and type(event) is Message:
            await db.store_message(event)
        result = await handler(event, data)
        logger.info("End StoreAllMessages")
        return result
