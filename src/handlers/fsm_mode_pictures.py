import logging
import keyboards.common as kb
from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.utils.formatting import Bold, as_list
from const.states import MainGroup
from const.text import cmd, msg, help

logger = logging.getLogger(__name__)
router = Router(name=__name__)


# Entering Pictures mode
@router.message(
    StateFilter(default_state), or_f(Command("pictures"), F.text == cmd["pictures"])
)
async def process_entering_mode_command(message: Message, state: FSMContext) -> None:
    logger.info("FSM: pictures: entering pictures mode")
    await state.set_state(MainGroup.pictures_mode)
    await message.answer(msg["pictures_main"], reply_markup=kb.get_pictures_kb())


# Help command for Pictures mode
@router.message(StateFilter(MainGroup.pictures_mode), Command("help"))
async def process_help_command(message: Message) -> None:
    logger.info("FSM: pictures: help command")
    await message.answer(
        **as_list(Bold(help["pictures_cmd"]), help["pictures_cancel"]).as_kwargs()
    )


# Cancel command for Pictures mode
@router.message(
    StateFilter(MainGroup.pictures_mode),
    (or_f(Command("cancel"), F.text == cmd["exit"])),
)
async def process_abonement_cancel_command(
    message: Message, state: FSMContext, user_type: list[str]
) -> None:
    logger.info("FSM: abonement: cancel command")
    await state.clear()
    await message.answer(
        text=msg["pictures_end"], reply_markup=kb.get_main_kb(user_type)
    )


#
#
# All handlers will be here
#
#


# Unknown command for Pictures mode
@router.message(StateFilter(MainGroup.pictures_mode))
async def process_unknown_command(message: Message) -> None:
    logger.info("FSM: pictures: unknown command")
    await message.answer(msg["pictures_unknown"])
