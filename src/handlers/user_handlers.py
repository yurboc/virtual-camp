import logging
import keyboards.common as kb
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.state import default_state

logger = logging.getLogger(__name__)
router = Router(name=__name__)


# Command /start on default state
@router.message(StateFilter(default_state), CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
        text=f"Вас приветствует бот Virtual Camp!\n" "Вы в главном меню.",
        reply_markup=kb.get_main_kb(),
    )


# Command /help on default state
@router.message(StateFilter(default_state), Command(commands=["help"]))
async def process_help_command(message: Message) -> None:
    await message.answer(
        f"Справка:\n"
        "Команда /diag - войти в диагностический режим.\n"
        "Команда /generate - начать генерацию таблиц.\n"
    )
