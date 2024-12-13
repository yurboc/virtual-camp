import os
import json
import pika
import uuid
import logging
from logging import handlers
from aiohttp import web
from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from config.config import config


LOG_FILE = config["LOG"]["VIRTUAL_CAMP_BOT"]["FILE"]
LOG_LEVEL = config["LOG"]["VIRTUAL_CAMP_BOT"]["LEVEL"]
LOG_FORMAT = (
    "%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s"
)
LOG_BACKUP_COUNT = 14
OUTGOING_QUEUE = "tasks_queue"

# Bot and Webserver settings
TOKEN = config["BOT"]["TOKEN"]
WEB_SERVER_HOST = config["BOT"]["WEB_SERVER_HOST"]
WEB_SERVER_PORT = config["BOT"]["WEB_SERVER_PORT"]
WEBHOOK_PATH = config["BOT"]["WEBHOOK_PATH"]
WEBHOOK_SECRET = config["BOT"]["WEBHOOK_SECRET"]
BASE_WEBHOOK_URL = config["BOT"]["BASE_WEBHOOK_URL"]

# Setup logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),  # write logs to console
        logging.handlers.TimedRotatingFileHandler(  # write logs to file
            LOG_FILE, when="midnight", backupCount=LOG_BACKUP_COUNT
        ),
    ],
)
logger = logging.getLogger(__name__)

# All handlers should be attached to the Router (or Dispatcher)
router = Router()


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
        f"Hello, {hbold(message.from_user.full_name)}!\n"
        "Use /generate to start.\n"
        "Use /help to get help."
    )


@router.message(Command(commands=["help"]))
async def process_help_command(message: Message) -> None:
    """
    This handler receives messages with `/help` command
    """
    await message.answer(f"Help command accepted.\nUse /generate to start.")


@router.message(Command(commands=["generate"]))
async def process_generate_command(message: Message) -> None:
    """
    This handler receives messages with `/generate` command
    """
    msg = {"uuid": str(uuid.uuid4()), "job": "all"}
    publish_message(msg)
    await message.answer(f"Generate command accepted, wait...")


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


async def on_startup(bot: Bot) -> None:
    await bot.set_webhook(
        f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}", secret_token=WEBHOOK_SECRET
    )


# MAIN
def main() -> None:
    logger.info(f"Starting VirtualCampBot with PID={os.getpid()}...")

    # Dispatcher is a root router
    dp = Dispatcher()
    # ... and all other routers should be attached to Dispatcher
    dp.include_router(router)

    # Register startup hook to initialize webhook
    dp.startup.register(on_startup)

    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # Create aiohttp.web.Application instance
    app = web.Application()

    # Create an instance of request handler,
    # aiogram has few implementations for different cases of usage
    # In this example we use SimpleRequestHandler which is designed to handle simple cases
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )
    # Register webhook handler on application
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    # Mount dispatcher startup and shutdown hooks to aiohttp application
    setup_application(app, dp, bot=bot)

    # And finally start webserver
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)

    # Stop bot
    logger.info("Finished VirtualCampBot!")


# Entry point
if __name__ == "__main__":
    main()
