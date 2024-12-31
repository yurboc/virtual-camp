import logging
import keyboards.common as kb
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.utils.formatting import Text, Pre, as_list, as_marked_list, as_key_value
from handlers.fsm_define import MainGroup
from storage.db_api import Database

logger = logging.getLogger(__name__)
router = Router(name=__name__)


# Entering diagnostic mode
@router.message(StateFilter(default_state), Command(commands=["diag"]))
async def process_diag_command(message: Message, state: FSMContext) -> None:
    logger.info(f"FSM: diag: entering diag mode")
    await state.set_state(MainGroup.diag_mode)
    await message.answer(
        text="Диагностика. Выход - /cancel",
        reply_markup=kb.no_keyboard,
    )


# Command /help in diag state
@router.message(StateFilter(MainGroup.diag_mode), Command(commands=["help"]))
async def process_help_command(message: Message):
    logger.info(f"FSM: diag: help command")
    await message.answer(
        **Text(
            as_list(
                "Справка:",
                "/cancel - завершить диагностику",
                "/info - информация о пользователе",
            )
        ).as_kwargs(),
    )


# Command /cancel in diag state
@router.message(StateFilter(MainGroup.diag_mode), Command(commands=["cancel"]))
async def process_cancel_command(
    message: Message, state: FSMContext, user_type: list[str]
):
    logger.info(f"FSM: diag: cancel command, user_type={user_type}")
    await state.clear()
    await message.answer(
        text="Завершение диагностики. Вы в главном меню.",
        reply_markup=kb.get_main_kb(user_type),
    )


# Command /info in diag state
@router.message(StateFilter(MainGroup.diag_mode), Command(commands=["info"]))
async def process_info_command(
    message: Message, db: Database, user_id: int, user_type: list[str]
) -> None:
    logger.info(f"FSM: diag: info command, user_id={user_id}, user_type={user_type}")
    user = await db.user_by_tg_id(tg_id=user_id)
    content = Text(
        f"Пользователь. Выход - /cancel\n",
        as_marked_list(
            as_key_value("user_id", user_id),
            as_key_value("user_type", user_type),
        ),
        Pre(user),
    )
    await message.answer(
        **content.as_kwargs(),
        reply_markup=kb.no_keyboard,
    )


# All other messages in diag state
@router.message(StateFilter(MainGroup.diag_mode))
async def process_any_message(message: Message) -> None:
    logger.info(f"FSM: diag: any message")
    content = Text(
        "Расшифровка. Выход - /cancel",
        Pre(message.model_dump_json(indent=4, exclude_none=True), language="JSON"),
    )
    await message.answer(
        **content.as_kwargs(),
        reply_markup=kb.no_keyboard,
    )
