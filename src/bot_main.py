import asyncio
import os
import logging
import logging.handlers
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage, Redis
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine
from middleware.outer import DatabaseMiddleware, StoreAllUpdates, CheckUserType
from middleware.inner import StoreAllMessages
from handlers import other_handlers, user_handlers
from storage import db_schema
from config.config import config


# Logging settings
LOG_FILE = config["LOG"]["BOT"]["FILE"]
LOG_LEVEL = config["LOG"]["BOT"]["LEVEL"]
LOG_FORMAT = (
    "%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s"
)
LOG_BACKUP_COUNT = 14

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
logging.getLogger("pika").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# Startup handler
async def on_startup(bot: Bot) -> None:
    await bot.set_webhook(
        f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}", secret_token=WEBHOOK_SECRET
    )


# MAIN
async def async_main() -> None:
    logger.info(f"Starting VirtualCampBot with PID={os.getpid()}...")

    # Setup DB
    db_url = URL.create(
        config["DB"]["TYPE"],
        username=config["DB"]["USERNAME"],
        password=config["DB"]["PASSWORD"],
        host=config["DB"]["HOST"],
        database=config["DB"]["NAME"],
    )
    async_engine: AsyncEngine = create_async_engine(db_url, echo=False)

    # Create DB structure
    async with async_engine.begin() as conn:
        # DROP TABLES: await conn.run_sync(db_schema.Base.metadata.drop_all)
        await conn.run_sync(db_schema.Base.metadata.create_all)

    # Create internal objects
    redis = Redis(host="localhost")
    storage = RedisStorage(redis=redis)
    async_session = async_sessionmaker(async_engine, expire_on_commit=False)
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=storage, engine=async_engine)

    # Add routers
    dp.include_router(user_handlers.router)
    dp.include_router(other_handlers.router)

    # Add middleware
    dp.update.outer_middleware(DatabaseMiddleware(session=async_session))
    dp.update.outer_middleware(StoreAllUpdates())
    dp.message.outer_middleware(CheckUserType())
    dp.message.middleware(StoreAllMessages())

    # Configure webhook
    logger.info("Setting up webhook...")

    # Register startup hook to initialize webhook
    dp.startup.register(on_startup)

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
    # web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)
    await site.start()

    # wait forever
    await asyncio.Event().wait()

    # Stop bot
    logger.info("Finished VirtualCampBot!")


# Entry point
if __name__ == "__main__":
    asyncio.run(async_main())
