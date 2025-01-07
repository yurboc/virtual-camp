import logging
import keyboards.common as kb
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.utils.formatting import Text, Bold, as_list
from const.text import msg, help

logger = logging.getLogger(__name__)
router = Router(name=__name__)


# Command /start on default state
@router.message(StateFilter(default_state), CommandStart())
async def command_start_handler(message: Message, user_type: list[str]) -> None:
    logger.info("Got START command")
    await message.answer(
        **Text(as_list(msg["hello_bot"], "", msg["main_menu"])).as_kwargs(),
        reply_markup=kb.get_main_kb(user_type),
    )


# Command /help on default state
@router.message(StateFilter(default_state), Command("help"))
async def process_help_command(message: Message) -> None:
    logger.info("Got HELP command")
    await message.answer(
        **Text(
            as_list(
                Bold(help["all_cmd"]),
                help["all_start"],
                help["all_help"],
                help["all_cancel"],
                Bold(help["my_cmd"]),
                help["my_diag"],
                help["my_register"],
                help["my_tables"],
                help["my_abonement"],
            )
        ).as_kwargs()
    )


# Command cancel in WRONG state (not handled active process)
@router.message(~StateFilter(default_state), Command("cancel"))
async def send_state_cancel_answer(message: Message, state: FSMContext):
    logger.warning("Got CANCEL command in WRONG state")
    logger.warning(f"State: {await state.get_state()}")
    await state.clear()
    await message.answer(text=msg["failure"])
