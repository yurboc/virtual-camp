import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

logger = logging.getLogger(__name__)
router = Router(name=__name__)
help_str = "\n\nОтправьте /help для справки."


# Default cancel (no active processes)
@router.message(Command("cancel"))
async def send_cancel_answer(message: Message):
    await message.answer(text="Нет активных процессов." + help_str)


# Default handler (for all other messages)
@router.message()
async def send_default_answer(message: Message):
    await message.answer(text="Сообщение не распознано." + help_str)
