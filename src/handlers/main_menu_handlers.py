import logging
import keyboards.common as kb
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.utils.formatting import Text, Bold, as_list

logger = logging.getLogger(__name__)
router = Router(name=__name__)


# Command /start on default state
@router.message(StateFilter(default_state), CommandStart())
async def command_start_handler(message: Message, user_type: list[str]) -> None:
    logger.info(f"Got START command")
    await message.answer(
        **Text(
            as_list("Вас приветствует бот Virtual Camp!", "", "Вы в главном меню.")
        ).as_kwargs(),
        reply_markup=kb.get_main_kb(user_type),
    )


# Command /help on default state
@router.message(StateFilter(default_state), Command("help"))
async def process_help_command(message: Message) -> None:
    logger.info(f"Got HELP command")
    await message.answer(
        **Text(
            as_list(
                Bold("Общие команды:"),
                "/start - запуск бота",
                "/help - справка по текущему режиму",
                "/cancel - выход из текущего режима",
                Bold("Вам доступны режимы:"),
                "/diag - диагностика бота",
                "/register - регистрация пользователя",
                "/generate - генерация таблиц ФСТ-ОТМ",
                "/abonement - подсчет посещений и абонементы",
            )
        ).as_kwargs()
    )


# Command cancel in WRONG state (not handled active process)
@router.message(~StateFilter(default_state), Command("cancel"))
async def send_state_cancel_answer(message: Message, state: FSMContext):
    logger.warning(f"Got CANCEL command in WRONG state")
    logger.warning(f"State: {await state.get_state()}")
    await state.clear()
    await message.answer(text="Обнаружен сбой. Отправьте команду /start")
