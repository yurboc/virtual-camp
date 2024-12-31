import logging
import json
import pika
import uuid
import keyboards.common as kb
from typing import Optional
from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.utils.formatting import Text, as_list, as_key_value
from handlers.fsm_define import MainGroup
from storage.db_api import Database
from utils.config import config, tables

logger = logging.getLogger(__name__)
router = Router(name=__name__)


# Entering Climbing zone pass Counter mode
@router.message(
    StateFilter(default_state),
    or_f(Command(commands=["counter"]), F.text == "Абонементы"),
)
async def process_generator_command(message: Message, state: FSMContext) -> None:
    logger.info(f"FSM: counter: entering counter mode")
    await state.set_state(MainGroup.counter_mode)
    await message.answer(
        **Text(
            as_list(
                "Подсчет посещений по абонементам",
                "Выберите абонемент для подсчета",
            )
        ).as_kwargs(),
        reply_markup=kb.get_counter_kb(),
    )


# Help command for Counter
@router.message(StateFilter(MainGroup.counter_mode), Command(commands=["help"]))
async def process_help_command(message: Message) -> None:
    logger.info(f"FSM: counter: help command")
    content = Text("Справка: выберите абонемент из списка")
    await message.answer(**content.as_kwargs())


# Cancel command for Counter
@router.message(
    StateFilter(MainGroup.counter_mode),
    (or_f(Command(commands=["cancel"]), F.text == "Выход", F.text == "Главное меню")),
)
async def process_cancel_command(message: Message, state: FSMContext) -> None:
    logger.info(f"FSM: counter: cancel command")
    await state.clear()
    await message.answer(
        text="Завершение работы с абонементами. Вы в главном меню.",
        reply_markup=kb.get_main_kb(),
    )


# Unknown command for Counter
@router.message(StateFilter(MainGroup.counter_mode))
async def process_unknown_command(message: Message) -> None:
    await message.answer(
        "Неизвестная команда работы с абонементами.\nСправка - /help\nВыход - /cancel"
    )
