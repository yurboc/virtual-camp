import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from const.text import msg
from aiogram.utils.formatting import as_list

logger = logging.getLogger(__name__)
router = Router(name=__name__)


# Default cancel (no active processes)
@router.message(Command("cancel"))
async def send_cancel_answer(message: Message):
    await message.answer(**as_list(msg["no_proc"], msg["help"]).as_kwargs())


# Default handler (for all other messages)
@router.message()
async def send_default_answer(message: Message):
    await message.answer(**as_list(msg["unknown"], msg["help"]).as_kwargs())
