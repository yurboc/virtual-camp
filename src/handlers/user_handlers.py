import logging
import keyboards.common as kb
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.utils.formatting import Text, Pre, as_list, as_marked_list, as_key_value

logger = logging.getLogger(__name__)
router = Router(name=__name__)


# Command /start on default state
@router.message(StateFilter(default_state), CommandStart())
async def command_start_handler(message: Message) -> None:
    logger.info(f"Got START command")
    await message.answer(
        text=f"Вас приветствует бот Virtual Camp!\n" "Вы в главном меню.",
        reply_markup=kb.get_main_kb(),
    )


# Command /help on default state
@router.message(StateFilter(default_state), Command(commands=["help"]))
async def process_help_command(message: Message) -> None:
    logger.info(f"Got HELP command")
    await message.answer(
        Text(
            as_list(
                "Справка:",
                "/start - начать работу с ботом.",
                "/help - вывести справку по текущему режиму.",
                "/cancel - завершить текущий процесс.",
                "/diag - войти в диагностический режим.",
                "/generate - войти в режим генерации таблиц.",
                "/abonement - войти в режим работы с абонементами.",
            )
        )
    )


# Command cancel in WRONG state (not handled active process)
@router.message(~StateFilter(default_state), Command(commands=["cancel"]))
async def send_state_cancel_answer(message: Message, state: FSMContext):
    logger.warning(f"Got CANCEL command in WRONG state")
    logger.warning(f"State: {await state.get_state()}")
    await state.clear()
    await message.answer(text="Обнаружен сбой. Отправьте команду /start")
