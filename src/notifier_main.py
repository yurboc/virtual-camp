import asyncio
import logging
import pika
import os
import json
import logging.handlers
from aiogram import Bot
from config.config import config

# Settings
TOKEN = config["BOT"]["TOKEN"]
ADMIN_ID = config["BOT"]["ADMIN"]
LOG_FILE = config["LOG"]["NOTIFIER"]["FILE"]
LOG_LEVEL = config["LOG"]["NOTIFIER"]["LEVEL"]
LOG_FORMAT = (
    "%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s"
)
LOG_BACKUP_COUNT = 14
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

bot = Bot(token=TOKEN)


# Send message to Telegram
async def send_message(chat_id, text):
    logger.info("Prepare Telegram message...")
    try:
        await bot.send_message(chat_id=chat_id, text=text)
    except:
        logger.warning("Error sending Telegram message", exc_info=True)
    await bot.session.close()
    logger.info("Telegram message sent!")


# Handle new message
def on_new_message(ch, method, properties, body):
    # Decode incoming message
    logger.info("Got new RabbitMQ message...")
    try:
        msg = json.loads(body.decode())
        msg_uuid = msg.get("uuid", "no_uuid")
    except:
        logger.warning(
            f"Error decoding incoming RabbitMQ message: {body.decode()}", exc_info=True
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return
    # Get message UUID
    logger.info(f"Got RabbitMQ message with UUID '{msg_uuid}'...")
    logger.info(body.decode())
    # Prepare message text
    msg_text = "Получен результат генерации:\n\n"
    if msg.get("uuid"):
        msg_text += f"UUID: {msg['uuid']}\n"
    if msg.get("job"):
        msg_text += f"Задание: {msg['job']}\n"
    if msg.get("table"):
        msg_text += f"Таблица: {msg['table']}\n"
    if msg.get("result"):
        msg_text += f"Результат: {msg['result']}\n"
    if msg.get("uuuuhz"):
        msg_text += f"Хзхз: {msg['uuuuhz']}\n"
    asyncio.run(
        send_message(
            chat_id=ADMIN_ID,
            text=msg_text,
        )
    )
    ch.basic_ack(delivery_tag=method.delivery_tag)
    logger.info("Done RabbitMQ message processing!")


# MAIN
def main():
    logger.info(f"Starting queue notifier with PID={os.getpid()}...")
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()
    channel.queue_declare(queue=INCOMING_QUEUE)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=INCOMING_QUEUE, on_message_callback=on_new_message)
    logger.info("Worker started, waiting for messages...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()
    logger.info("Finished queue notifier!")


# Entry point
if __name__ == "__main__":
    main()
