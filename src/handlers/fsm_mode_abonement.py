import logging
import keyboards.common as kb
from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.utils.formatting import Text, Code, as_list, as_key_value
from handlers.fsm_define import MainGroup
from storage.db_api import Database

logger = logging.getLogger(__name__)
router = Router(name=__name__)


# Entering Abonement mode
@router.message(
    StateFilter(default_state),
    or_f(Command(commands=["abonement"]), F.text == "Абонементы"),
)
async def process_abonement_command(message: Message, state: FSMContext) -> None:
    logger.info(f"FSM: abonement: entering abonement mode")
    await state.set_state(MainGroup.abonement_mode)
    await message.answer(
        **Text(
            as_list(
                "Подсчет посещений по абонементам",
                "Выберите абонемент для подсчета",
            )
        ).as_kwargs(),
        reply_markup=kb.get_abonement_kb(),
    )


# Help command for Abonement
@router.message(StateFilter(MainGroup.abonement_mode), Command(commands=["help"]))
async def process_abonement_help_command(message: Message) -> None:
    logger.info(f"FSM: abonement: help command")
    content = Text("Справка: выберите абонемент из списка")
    await message.answer(**content.as_kwargs())


# Cancel command for Abonement
@router.message(
    StateFilter(MainGroup.abonement_mode),
    (or_f(Command(commands=["cancel"]), F.text == "Выход")),
)
async def process_abonement_cancel_command(message: Message, state: FSMContext) -> None:
    logger.info(f"FSM: abonement: cancel command")
    await state.clear()
    await message.answer(
        text="Завершение работы с абонементами. Вы в главном меню.",
        reply_markup=kb.get_main_kb(),
    )


# List of Abonement
@router.message(StateFilter(MainGroup.abonement_mode), F.text == "Мои абонементы")
async def process_my_abonements_command(
    message: Message, user_id: int, db: Database
) -> None:
    logger.info(f"FSM: abonement: list my abonements")
    user = await db.user_by_tg_id(user_id)
    abonements = await db.abonements_list_by_owner(user)
    abonements_list = [
        f"{abonement.id}. {abonement.name}\nНа {abonement.total_passes} посещений\nToken: {abonement.token}"
        for abonement in abonements
    ]
    content = Text(as_list("Список моих абонементов:", *abonements_list))
    await message.answer(**content.as_kwargs())


# Add new Abonement
@router.message(StateFilter(MainGroup.abonement_mode), F.text == "Создать абонемент")
async def process_add_abonement_command(
    message: Message, user_id: int, db: Database
) -> None:
    logger.info(f"FSM: abonement: add new abonement")
    user = await db.user_by_tg_id(user_id)
    abonement = await db.abonement_create(
        name="Название абонемента", owner=user, total_passes=100
    )
    await message.answer(
        **Text(
            as_list(
                "Новый абонемент создан:", as_key_value("Token", Code(abonement.token))
            )
        ).as_kwargs()
    )


# Unknown command for Abonement
@router.message(StateFilter(MainGroup.abonement_mode))
async def process_abonement_unknown_command(message: Message) -> None:
    await message.answer(
        "Неизвестная команда работы с абонементами.\nСправка - /help\nВыход - /cancel"
    )
