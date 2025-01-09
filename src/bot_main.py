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
from handlers import (
    deep_link_handlers,
    fsm_main_handlers,
    fsm_mode_invites,
    fsm_mode_pictures,
    other_handlers,
    fsm_mode_diag,
    fsm_mode_register,
    fsm_mode_generator,
    fsm_mode_abonement,
    fsm_mode_abonement_cb,
)
from storage import db_schema
from utils.config import config
from utils.log import setup_logger

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
    dp = Dispatcher(storage=storage, engine=async_engine)

    # Add routers
    dp.include_router(fsm_mode_diag.router)  # Diag mode (always first)
    dp.include_router(deep_link_handlers.router)  # Deep links (always second)
    dp.include_router(fsm_mode_register.router)  # Register user
    dp.include_router(fsm_mode_invites.router)  # Invite user
    dp.include_router(fsm_mode_generator.router)  # FST-OTM tables generator
    dp.include_router(fsm_mode_pictures.router)  # Picture  generation mode
    dp.include_router(fsm_mode_abonement_cb.router)  # Abonement: callbacks
    dp.include_router(fsm_mode_abonement.router)  # Abonement: messages
    dp.include_router(fsm_main_handlers.router)  # Main menu (always pre-last)
    dp.include_router(other_handlers.router)  # Other messages (always last)

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
    await asyncio.Event().wait()

    # Stop bot
    logger.info("Finished VirtualCampBot!")


# Entry point
if __name__ == "__main__":
    asyncio.run(async_main())
