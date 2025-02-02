import json
import pika
import logging
from utils.config import config

logger = logging.getLogger(__name__)


# Publish message to RabbitMQ
def publish(msg: dict, queue_name: str) -> None:
    message_json = json.dumps(msg)
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()
    channel.queue_declare(queue=config["RABBITMQ"]["QUEUES"][queue_name])
    channel.basic_publish(
        exchange="",
        routing_key=config["RABBITMQ"]["QUEUES"][queue_name],
        body=message_json,
    )
    connection.close()


# Publish RESULT to RabbitMQ
def result(msg: dict) -> None:
    logger.info("Publishing result to queue...")
    publish(msg, "RESULTS")
    logger.info("Done publishing result to queue!")


# Publish TASK to RabbitMQ
def task(msg: dict) -> None:
    logger.info("Publishing task to queue...")
    publish(msg, "TASKS")
    logger.info("Done publishing task to queue!")
