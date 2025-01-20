import logging
from aiogram import F, Router
from aiogram.types import Message, ErrorEvent
from aiogram.filters import Command
from aiogram.utils.formatting import as_list
from const.text import msg, re_uuid
from modules.help_menu import generate_top_level_help

logger = logging.getLogger(__name__)
router = Router(name=__name__)


# Default token handler
@router.message(F.text.regexp(re_uuid))
async def send_token_answer(message: Message):
    logger.info("Got unexpected TOKEN in message")
    await message.answer(msg["err_start_token"])


# Command /cancel (no active processes)
@router.message(Command("cancel"))
async def send_cancel_answer(message: Message):
    logger.info("Got CANCEL command")
    await message.answer(
        **as_list(msg["no_proc"], msg["help"], msg["start"]).as_kwargs()
    )


# Command /help (not handled in other handlers)
@router.message(Command("help"))
async def process_help_command(message: Message, user_type: list[str]) -> None:
    logger.info("Got HELP command")
    help = generate_top_level_help(user_type)
    await message.answer(**help.as_kwargs())


# Default handler (for all other messages)
@router.message()
async def send_default_answer(message: Message):
    logger.info("Got UNKNOWN command")
    await message.answer(
        **as_list(msg["unknown"], msg["help"], msg["cancel"]).as_kwargs()
    )


# Handle Telegram errors
@router.error()
async def error_handler(event: ErrorEvent):
    logger.warning("Unhandled error caused by %s", event.exception, exc_info=True)
