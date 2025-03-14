import sentry_sdk
import asyncio
import os
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
from storage import db_schema
from utils.config import config
from utils.log import setup_logger
from handlers import (
    start_handlers,
    fsm_diag,
    fsm_register,
    fsm_invites,
    fsm_tables,
    fsm_pictures,
    fsm_abonement_cb,
    fsm_abonement,
    other_handlers,
)

# Setup Sentry
sentry_sdk.init(config["SENTRY"]["DSN"])

# Setup logging
logger = setup_logger(
    name=__name__,
    file=config["LOG"]["BOT"]["FILE"],
    level=config["LOG"]["BOT"]["LEVEL"],
)


# Startup handler
async def on_startup(bot: Bot) -> None:
    await bot.set_webhook(
        f'{config["BOT"]["BASE_WEBHOOK_URL"]}{config["BOT"]["WEBHOOK_PATH"]}',
        secret_token=config["BOT"]["WEBHOOK_SECRET"],
    )


# Configure and start webhook
async def start_as_webhook(dp: Dispatcher, bot: Bot) -> None:
    logger.info("Setting up webhook...")

    # Register startup hook to initialize webhook
    dp.startup.register(on_startup)

    # Create aiohttp.web.Application instance
    app = web.Application()

    # Create an instance of request handler
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=config["BOT"]["WEBHOOK_SECRET"],
    )

    # Register webhook handler on application
    webhook_requests_handler.register(app, path=config["BOT"]["WEBHOOK_PATH"])

    # Mount dispatcher startup and shutdown hooks to aiohttp application
    setup_application(app, dp, bot=bot)

    # And finally start webserver
    # web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(
        runner,
        host=config["BOT"]["WEB_SERVER_HOST"],
        port=config["BOT"]["WEB_SERVER_PORT"],
    )
    await site.start()

    # wait forever
    logger.info("Bot started!")
    await asyncio.Event().wait()


# MAIN
async def async_main() -> None:
    logger.info("Starting bot with PID=%d...", os.getpid())

    # Setup DB
    db_url = URL.create(
        config["DB"]["TYPE"],
        username=config["DB"]["USERNAME"],
        password=config["DB"]["PASSWORD"],
        host=config["DB"]["HOST"],
        database=config["DB"]["NAME"],
    )
    async_engine: AsyncEngine = create_async_engine(db_url, echo=False)

    # Create DB structures
    async with async_engine.begin() as conn:
        # DROP TABLES: await conn.run_sync(db_schema.Base.metadata.drop_all)
        await conn.run_sync(db_schema.Base.metadata.create_all)

    # Create internal objects
    redis = Redis(host="localhost")
    storage = RedisStorage(redis=redis)
    async_session = async_sessionmaker(async_engine, expire_on_commit=False)
    bot = Bot(
        token=config["BOT"]["TOKEN"],
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage, engine=async_engine, bot=bot)
    bot_name = await bot.get_my_name()
    logger.info("Created bot %s", bot_name)

    # Add routers
    dp.include_router(start_handlers.router)  # START and deep-linking
    dp.include_router(fsm_diag.router)  # Diag mode
    dp.include_router(fsm_register.router)  # Register user
    dp.include_router(fsm_invites.router)  # Invite user
    dp.include_router(fsm_tables.router)  # FST-OTM tables generator
    dp.include_router(fsm_pictures.router)  # Picture  generation mode
    dp.include_router(fsm_abonement_cb.router)  # Abonement: callbacks
    dp.include_router(fsm_abonement.router)  # Abonement: messages
    dp.include_router(other_handlers.router)  # Other messages

    # Add middleware
    dp.update.outer_middleware(DatabaseMiddleware(session=async_session))
    dp.update.outer_middleware(StoreAllUpdates())
    dp.message.outer_middleware(CheckUserType())
    dp.message.middleware(StoreAllMessages())

    # Select bot mode
    if config["BOT"]["MODE"] == "webhook":
        logger.info("Set mode: webhook")
        await start_as_webhook(dp, bot)
    elif config["BOT"]["MODE"] == "polling":
        logger.info("Set mode: polling")
        await bot.delete_webhook(drop_pending_updates=False)
        await dp.start_polling(bot)

    # Stop bot
    logger.info("Finished VirtualCampBot!")


# Entry point
if __name__ == "__main__":
    asyncio.run(async_main())
