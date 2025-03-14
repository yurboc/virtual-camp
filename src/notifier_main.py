import sentry_sdk
import asyncio
import os
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from utils.config import config
from storage.db_schema import Base
from modules.queue_consumer import QueueConsumer
from utils.log import setup_logger

# Setup Sentry
sentry_sdk.init(config["SENTRY"]["DSN"])

# Setup logging
logger = setup_logger(
    name=__name__,
    file=config["LOG"]["NOTIFIER"]["FILE"],
    level=config["LOG"]["NOTIFIER"]["LEVEL"],
)

# Setup DB
url: URL = URL.create(
    config["DB"]["TYPE"],
    username=config["DB"]["USERNAME"],
    password=config["DB"]["PASSWORD"],
    host=config["DB"]["HOST"],
    database=config["DB"]["NAME"],
)
engine = create_async_engine(url, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


# MAIN
async def main():
    logger.info(f"Starting queue notifier with PID={os.getpid()}...")

    # Initialize DB
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Setup RabbitMQ consumer
    logger.info("Starting RabbitMQ consumer...")
    consumer = QueueConsumer(
        url=config["RABBITMQ"]["URL"],
        queue_name=config["RABBITMQ"]["QUEUES"]["RESULTS"],
        bot_token=config["BOT"]["TOKEN"],
        admin_id=config["BOT"]["ADMIN"],
        session_maker=AsyncSessionLocal,
    )
    logger.info("Worker started, waiting for messages...")
    await consumer.start()

    # Exit
    consumer.stop()
    logger.info("Finished queue notifier!")


# Entry point
if __name__ == "__main__":
    asyncio.run(main())
