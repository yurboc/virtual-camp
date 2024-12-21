import logging
import json
import pika
import uuid
from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.utils.markdown import hbold
from storage.db_api import Database

logger = logging.getLogger(__name__)
router = Router(name=__name__)

# Queue settings
OUTGOING_QUEUE = "tasks_queue"


# Publish message
def publish_message(msg):
    logger.info("Publishing message...")
    message_json = json.dumps(msg)
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()
    channel.queue_declare(queue=OUTGOING_QUEUE)
    channel.basic_publish(
        exchange="",
        routing_key=OUTGOING_QUEUE,
        body=message_json,
    )
    connection.close()
    logger.info("Done publishing message!")


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(
        f"Привет, {hbold(message.from_user.full_name)}!\n"
        "Введите /generate для генерации всех таблиц.\n"
        "Введите /help для справки."
    )


@router.message(Command(commands=["help"]))
async def process_help_command(message: Message) -> None:
    """
    This handler receives messages with `/help` command
    """
    await message.answer(f"Справка:\nИспользуйте команду /generate чтобы начать генерацию таблиц.")


@router.message(Command(commands=["generate"]))
async def process_generate_command(message: Message) -> None:
    """
    This handler receives messages with `/generate` command
    """
    msg = {"uuid": str(uuid.uuid4()), "job": "all"}
    publish_message(msg)
    await message.answer(f"Генерация запущена, ждите...")


@router.message()
async def echo_handler(message: Message) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like text, photo, sticker etc.)
    """
    try:
        # Send a copy of the received message
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        # But not all the types is supported to be copied so need to handle it
        await message.answer("Nice try!")
