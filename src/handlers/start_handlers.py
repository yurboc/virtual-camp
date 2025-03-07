import logging
import keyboards.reply as kb
import keyboards.inline as ikb
import re
from typing import Optional, Union
from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.filters import CommandStart, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.utils.formatting import Bold, Italic, as_list
from const.text import msg
from const.formats import re_uuid
from modules import deep_linking as dl
from storage.db_api import Database

logger = logging.getLogger(__name__)
router = Router(name=__name__)


# Command /start (deep linking)
@router.message(CommandStart(deep_link=True))
async def start_with_deep_link_handler(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    db: Database,
    user_id: int,
    user_type: list[str],
) -> None:
    logger.info("Got deep-linking START: {}".format(command.args))
    args = command.args.split("_") if command.args else []
    # Clear state and return to main menu
    await state.clear()
    await message.answer(msg["linking_main"], reply_markup=kb.get_main_kb(user_type))
    # Mode 'abonement': try to join to Abonement of another user
    if len(args) == 2 and args[0] == "abonement" and re.search(re_uuid, args[1]):
        abonement, text = await dl.handle_abonement(args[1], db, user_id)
        answer_kb: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None
        if abonement:
            answer_kb = ikb.get_abonement_items_kb([abonement])
        else:
            answer_kb = kb.get_main_kb(user_type)
        await message.answer(**text.as_kwargs(), reply_markup=answer_kb)
    # Mode 'invite': add user to priveleged group
    elif len(args) == 2 and args[0] == "invite" and re.search(re_uuid, args[1]):
        _, text = await dl.handle_invite(args[1], db, user_id, user_type)
        await message.answer(**text.as_kwargs(), reply_markup=kb.get_main_kb(user_type))
    # Default: start with wrong parameters
    else:
        text = as_list(msg["hello_bot"], Italic(msg["err_params"]), msg["main_menu"])
        await message.answer(**text.as_kwargs(), reply_markup=kb.get_main_kb(user_type))


# Command /start (default state)
@router.message(CommandStart(), StateFilter(default_state))
async def command_start_default_handler(message: Message, user_type: list[str]) -> None:
    logger.info("Got START command!")
    await message.answer(
        **as_list(msg["hello_bot"], "", msg["main_menu"]).as_kwargs(),
        reply_markup=kb.get_main_kb(user_type),
    )


# Command /start (any other state)
@router.message(CommandStart())
async def command_start_from_mode_handler(
    message: Message, state: FSMContext, user_type: list[str]
) -> None:
    logger.info("Got START command in {} state".format(await state.get_state()))
    await state.clear()
    await message.answer(
        **as_list(msg["hello_bot"], "", Bold(msg["main_menu_exit"])).as_kwargs(),
        reply_markup=kb.get_main_kb(user_type),
    )
