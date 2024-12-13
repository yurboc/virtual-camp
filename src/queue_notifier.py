import logging
import pika
import os
import json
from logging import handlers
from aiogram import Bot, Dispatcher
from config.config import config

LOG_FILE = config["LOG"]["QUEUE_NOTIFIER"]["FILE"]
LOG_LEVEL = config["LOG"]["QUEUE_NOTIFIER"]["LEVEL"]
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


# Handle new message
def on_new_message(ch, method, properties, body):
    # Decode incoming message
    logger.info("Got new message...")
    try:
        msg = json.loads(body.decode())
        msg_uuid = msg.get("uuid", "no_uuid")
    except:
        logger.warning(
            f"Error decoding incoming message: {body.decode()}", exc_info=True
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return
    # Get message UUID
    logger.info(f"Got message with UUID '{msg_uuid}'...")
    logger.info(body.decode())
    ch.basic_ack(delivery_tag=method.delivery_tag)
    logger.info("Done message processing!")


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
