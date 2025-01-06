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

# Get possible jobs
possible_jobs = []
for table in tables:
    possible_jobs.append(table["title"])
possible_jobs.append("Все")


# Get job by name
def get_job_by_name(title: Optional[str]) -> Optional[str]:
    if title is None:
        return None
    for table in tables:
        if table["title"] == title:
            return table["generator_name"]
    if title == "Все":
        return "all"
    return None


# Publish RabbitMQ message
def queue_publish_message(msg: dict) -> None:
    logger.info("Publishing message...")
    message_json = json.dumps(msg)
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()
    channel.queue_declare(queue=config["RABBITMQ"]["QUEUES"]["TASKS"])
    channel.basic_publish(
        exchange="",
        routing_key=config["RABBITMQ"]["QUEUES"]["TASKS"],
        body=message_json,
    )
    connection.close()
    logger.info("Done publishing message!")


# Entering FST-OTM Tables Generator mode
@router.message(
    StateFilter(default_state),
    or_f(Command("generate"), F.text == "Генератор таблиц"),
)
async def process_generator_command(message: Message, state: FSMContext) -> None:
    logger.info(f"FSM: generator: entering generator mode")
    await state.set_state(MainGroup.generator_mode)
    await message.answer(
        **Text(
            as_list(
                "Генерация таблиц ФСТ-ОТМ",
                "Выберите таблицу для генерации",
            )
        ).as_kwargs(),
        reply_markup=kb.get_generator_kb(),
    )


# Selected table for Generator
@router.message(StateFilter(MainGroup.generator_mode), F.text.in_(possible_jobs))
async def process_selected_table(
    message: Message, state: FSMContext, db: Database, user_id: int
) -> None:
    logger.info(f"FSM: generator: selected table {message.text}")
    job = get_job_by_name(message.text)
    if job is None:
        await message.answer("Задание неверное. Выход - /cancel")
        return
    task_uuid = str(uuid.uuid4())
    user = await db.user_by_id(user_id)
    task = await db.task_add(task_uuid=task_uuid, user=user)
    msg = {
        "uuid": task_uuid,
        "task_id": task.id,
        "job_type": "table_generator",
        "job": job,
    }
    queue_publish_message(msg)
    await message.answer(
        **Text(
            as_list(
                "Генерация запущена, ждите.",
                as_key_value("ID задания", task.id),
                as_key_value("UUID", task_uuid),
            )
        ).as_kwargs(),
        reply_markup=kb.go_home_kb,
    )


# Help command for Generator
@router.message(StateFilter(MainGroup.generator_mode), Command("help"))
async def process_help_command(message: Message) -> None:
    logger.info(f"FSM: generator: help command")
    content_list = [Text("Режим работы с таблицами ФСТ-ОТМ:")]
    for table in tables:
        content_list.append(
            as_key_value(key=table["generator_name"], value=table["title"])
        )
    content_list.append(as_key_value(key="all", value="Все"))
    content = Text(as_list(*content_list))
    await message.answer(**content.as_kwargs())


# Cancel command for Generator
@router.message(
    StateFilter(MainGroup.generator_mode),
    (or_f(Command("cancel"), F.text.in_(["Выход", "Главное меню"]))),
)
async def process_cancel_command(
    message: Message, state: FSMContext, user_type: list[str]
) -> None:
    logger.info(f"FSM: generator: cancel command")
    await state.clear()
    await message.answer(
        text="Завершение генерации. Вы в главном меню.",
        reply_markup=kb.get_main_kb(user_type),
    )


# Unknown command for Generator
@router.message(StateFilter(MainGroup.generator_mode))
async def process_unknown_command(message: Message) -> None:
    await message.answer(
        "Неизвестная команда генерации.\nСправка - /help\nВыход - /cancel"
    )
