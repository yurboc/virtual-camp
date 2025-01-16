import logging
import keyboards.common as kb
from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.utils.formatting import Bold, as_list
from const.states import RegisterGroup
from storage.db_api import Database
from const.text import (
    cmd,
    msg,
    help,
    reg_main,
    reg_main_edit,
    reg_end,
    reg_phone,
    reg_name,
)

logger = logging.getLogger(__name__)
router = Router(name=__name__)


# Entering register mode
@router.message(
    StateFilter(default_state), or_f(Command("register"), F.text == cmd["register"])
)
async def process_register_command(
    message: Message, state: FSMContext, user_type: list[str]
) -> None:
    logger.info("FSM: register: entering register mode")
    await state.set_state(RegisterGroup.agreement)
    if "registered" in user_type:
        await message.answer(**reg_main_edit.as_kwargs(), reply_markup=kb.agreement_kb)
    else:
        await message.answer(**reg_main.as_kwargs(), reply_markup=kb.agreement_kb)


# Command /cancel in register state
@router.message(
    StateFilter(RegisterGroup),
    or_f(Command("cancel"), F.text.in_([cmd["disagree"], cmd["exit"]])),
)
async def process_cancel_command(
    message: Message, state: FSMContext, user_type: list[str]
):
    logger.info("FSM: register: cancel command")
    await state.clear()
    await message.answer(**reg_end.as_kwargs(), reply_markup=kb.get_main_kb(user_type))


# Command /help in register state
@router.message(StateFilter(RegisterGroup), Command("help"))
async def process_help_command(message: Message):
    logger.info("FSM: register: help command")
    await message.answer(
        **as_list(Bold(help["reg_cmd"]), help["reg_cancel"]).as_kwargs()
    )


# Got agreement, begin register
@router.message(StateFilter(RegisterGroup.agreement), F.text == cmd["agree"])
async def process_agreement(message: Message, state: FSMContext) -> None:
    logger.info("FSM: register: agreement")
    await state.set_state(RegisterGroup.phone)
    await message.answer(**reg_phone.as_kwargs(), reply_markup=kb.get_contact_kb)


# Wrong agreement
@router.message(StateFilter(RegisterGroup.agreement))
async def process_disagreement(message: Message, state: FSMContext) -> None:
    logger.info("FSM: register: disagreement")
    await message.answer(text=msg["reg_no_agree"], reply_markup=kb.agreement_kb)


# Got phone number
@router.message(StateFilter(RegisterGroup.phone), F.contact, F.reply_to_message)
async def process_phone(
    message: Message, state: FSMContext, db: Database, user_id: int
) -> None:
    logger.info("FSM: register: phone")
    await state.set_state(RegisterGroup.name)
    if message and message.contact and message.contact.phone_number:
        await state.update_data(phone=message.contact.phone_number)
    user = await db.user_by_id(user_id)
    if user and user.name:
        currentName = user.name
    elif message.from_user:
        currentName = message.from_user.full_name
    else:
        currentName = None
    await state.update_data(name=currentName)
    await message.answer(
        **reg_name(currentName).as_kwargs(),
        reply_markup=kb.empty_kb,
    )


# Wrong phone number
@router.message(StateFilter(RegisterGroup.phone))
async def process_wrong_phone(message: Message, state: FSMContext) -> None:
    logger.info("FSM: register: wrong phone")
    await message.answer(text=msg["reg_no_phone"], reply_markup=kb.get_contact_kb)


# Got name
@router.message(
    StateFilter(RegisterGroup.name), or_f(F.text.isprintable(), Command("skip"))
)
async def process_name(
    message: Message, state: FSMContext, db: Database, user_id: int
) -> None:
    logger.info("FSM: register: name")
    if message.text and message.text != "/skip":
        await state.update_data(name=message.text.strip())
    user_data = await state.get_data()
    user = await db.user_by_id(user_id)
    if not user:
        logger.warning(f"FSM: register: user {user_id} not found in DB")
        return
    user.tg_phone = user_data.get("phone")
    if user_data.get("name"):
        user.name = user_data.get("name")
    db.user_add_to_group(user, "registered")
    await db.user_update(user)
    await state.set_state(RegisterGroup.finish)
    await message.answer(text=msg["reg_done"], reply_markup=kb.go_home_kb)


# Wrong name
@router.message(StateFilter(RegisterGroup.name))
async def process_wrong_name(message: Message, state: FSMContext) -> None:
    logger.info("FSM: register: wrong name")
    await message.answer(text=msg["reg_no_name"])


# All other messages in register state
@router.message(StateFilter(RegisterGroup))
async def process_any_message(message: Message) -> None:
    logger.info("FSM: register: any message")
    await message.answer(text=msg["reg_unknown"])
