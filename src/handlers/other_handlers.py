import logging
from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.formatting import as_list
from const.text import msg, re_uuid

logger = logging.getLogger(__name__)
router = Router(name=__name__)


# Default token handler
@router.message(F.text.regexp(re_uuid))
async def send_token_answer(message: Message):
    await message.answer("Can't handle key without type")


# Default cancel (no active processes)
@router.message(Command("cancel"))
async def send_cancel_answer(message: Message):
    await message.answer(
        **as_list(msg["no_proc"], msg["help"], msg["start"]).as_kwargs()
    )


# Default handler (for all other messages)
@router.message()
async def send_default_answer(message: Message):
    await message.answer(
        **as_list(msg["unknown"], msg["help"], msg["cancel"]).as_kwargs()
    )
