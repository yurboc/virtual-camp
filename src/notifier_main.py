import asyncio
import os
import logging
import logging.handlers
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config.config import config
from storage.db_schema import Base
from modules.async_queue_client import AsyncQueueClient

# Settings
TOKEN = config["BOT"]["TOKEN"]
ADMIN_ID = config["BOT"]["ADMIN"]
LOG_FILE = config["LOG"]["NOTIFIER"]["FILE"]
LOG_LEVEL = config["LOG"]["NOTIFIER"]["LEVEL"]
LOG_FORMAT = (
    "%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s"
)
LOG_BACKUP_COUNT = 14
RABBITMQ_HOST = "amqp://localhost:5672/"
INCOMING_QUEUE = "results_queue"

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

# Setup DB
url: URL = URL.create(
    config["DB"]["TYPE"],
    username=config["DB"]["USERNAME"],
    password=config["DB"]["PASSWORD"],
    host=config["DB"]["HOST"],
    database=config["DB"]["NAME"],
)
engine = create_async_engine(url, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine)


# MAIN
async def main():
    logger.info(f"Starting queue notifier with PID={os.getpid()}...")

    # Initialize DB
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Setup RabbitMQ consumer
    logger.info("Starting RabbitMQ consumer...")
    client = AsyncQueueClient(
        url=RABBITMQ_HOST,
        queue_name=INCOMING_QUEUE,
        bot_token=TOKEN,
        admin_id=ADMIN_ID,
        session_maker=AsyncSessionLocal,
    )
    logger.info("Worker started, waiting for messages...")
    await client.start()

    # Exit
    client.stop()
    logger.info("Finished queue notifier!")


# Entry point
if __name__ == "__main__":
    asyncio.run(main())
