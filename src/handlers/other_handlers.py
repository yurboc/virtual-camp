import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

logger = logging.getLogger(__name__)
router = Router(name=__name__)
help_str = "Отправьте /help для справки."


# Default cancel
@router.message(Command(commands=["cancel"]))
async def send_cancel_answer(message: Message):
    await message.answer(text="Нет активных процессов.\n" + help_str)


# Default handler (for all other messages)
@router.message()
async def send_default_answer(message: Message):
    await message.answer(text="Сообщение не распознано.\n" + help_str)
