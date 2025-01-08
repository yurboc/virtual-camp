import logging
import keyboards.common as kb
from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.utils.formatting import (
    Text,
    Bold,
    Pre,
    as_list,
    as_marked_list,
    as_key_value,
    as_numbered_section,
)
from const.states import MainGroup
from storage.db_api import Database
from const.text import cmd, msg, help, user_types

logger = logging.getLogger(__name__)
router = Router(name=__name__)


# Entering diagnostic mode
@router.message(
    StateFilter(default_state), or_f(Command("diag"), F.text == cmd["diag"])
)
async def process_diag_command(message: Message, state: FSMContext) -> None:
    logger.info("FSM: diag: entering diag mode")
    await state.set_state(MainGroup.diag_mode)
    await message.answer(text=msg["diag_main"], reply_markup=kb.no_keyboard)


# Command /help in diag state
@router.message(StateFilter(MainGroup.diag_mode), Command("help"))
async def process_help_command(message: Message):
    logger.info("FSM: diag: help command")
    await message.answer(
        **Text(as_list(Bold(help["diag_cmd"]), help["diag_info"])).as_kwargs()
    )


# Command /cancel in diag state
@router.message(StateFilter(MainGroup.diag_mode), Command("cancel"))
async def process_cancel_command(
    message: Message, state: FSMContext, user_type: list[str]
):
    logger.info(f"FSM: diag: cancel command, user_type={user_type}")
    await state.clear()
    await message.answer(
        text=msg["diag_cancel"],
        reply_markup=kb.get_main_kb(user_type),
    )


# Command /info in diag state
@router.message(StateFilter(MainGroup.diag_mode), Command("info"))
async def process_info_command(
    message: Message, db: Database, user_id: int, user_tg_id: int, user_type: list[str]
) -> None:
    logger.info(f"FSM: diag: info command, user_id={user_id}, user_type={user_type}")
    user = await db.user_by_id(user_id)
    access_list: list[Text] = []
    for k, v in user_types.items():
        if k in user_type:
            access_list.append(Text(msg["m_yes"], v))
        else:
            access_list.append(Text(msg["m_no"], v))
    content = as_list(
        msg["diag_info"],
        as_marked_list(
            as_key_value("user_id", user_id),
            as_key_value("user_tg_id", user_tg_id),
            as_key_value("user_type", user_type),
        ),
        as_numbered_section(Bold(msg["access_list"]), *access_list),
        Pre(user),
    )
    await message.answer(
        **content.as_kwargs(),
        reply_markup=kb.no_keyboard,
    )


# All other messages in diag state
@router.message(StateFilter(MainGroup.diag_mode))
async def process_any_message(message: Message) -> None:
    logger.info("FSM: diag: any message")
    content = Text(
        msg["diag_any_msg"],
        Pre(message.model_dump_json(indent=4, exclude_none=True), language="JSON"),
    )
    await message.answer(
        **content.as_kwargs(),
        reply_markup=kb.no_keyboard,
    )
