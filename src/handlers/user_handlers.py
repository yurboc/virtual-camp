import logging
import json
import pika
import uuid
import keyboards.common as kb
from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.state import default_state
from storage.db_api import Database
from utils.config import config

logger = logging.getLogger(__name__)
router = Router(name=__name__)


# Publish message
def queue_publish_message(msg):
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


# Command /generate on default state
@router.message(Command(commands=["generate"]))
async def process_generate_command(
    message: Message, db: Database, user_id: int
) -> None:
    task_uuid = str(uuid.uuid4())
    user = await db.user_by_tg_id(user_id)
    task = await db.task_add(task_uuid=task_uuid, user=user)
    msg = {"uuid": task_uuid, "task_id": task.id, "job": "all"}
    queue_publish_message(msg)
    await message.answer(
        f"Генерация запущена, ждите...\nUUID: {task_uuid}\nID задания: {task.id}"
    )
