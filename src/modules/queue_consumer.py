import asyncio
import pika
import logging
import logging.handlers
from pika.adapters.asyncio_connection import AsyncioConnection
from modules.queue_handler import QueueHandler

logger = logging.getLogger(__name__)


class QueueConsumer:
    def __init__(self, url, queue_name, bot_token, admin_id, session_maker):
        self.url = url
        self.queue_name = queue_name
        self.connection = None
        self.channel = None
        self.handler = QueueHandler(bot_token, admin_id, session_maker)

    # Handle messages from RabbitMQ queue
    async def on_message_async(self, channel, method, properties, body):
        logger.info("Async handler started...")
        self.handler.convert_rabbitmq_message(body)  # sync handler (first)
        logger.info("Create notification...")
        await self.handler.create_notification()  # async handler (second)
        channel.basic_ack(delivery_tag=method.delivery_tag)
        logger.info("Message acked")

    async def start(self):
        logger.info("Create connection...")
        self.connection = self.connect()
        logger.info("Connection created")
        await asyncio.Future()  # Keep the event loop running

    def stop(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
        logger.info("Connection closed")

    def connect(self):
        return AsyncioConnection(
            pika.URLParameters(self.url),
            on_open_callback=self.on_connection_open,
            on_open_error_callback=self.on_connection_error,
            on_close_callback=self.on_connection_closed,
        )

    def on_connection_open(self, connection):
        logger.info("Connection established")
        self.connection = connection
        self.connection.channel(on_open_callback=self.on_channel_open)

    def on_connection_error(self, connection_unused, error_message=None):
        logger.error(f"Connection failed: {error_message}")

    def on_connection_closed(self, connection, reason):
        logger.error(f"Connection closed: {reason}")
        self.stop()

    def on_channel_open(self, channel):
        logger.info("Channel opened")
        self.channel = channel
        self.channel.basic_qos(prefetch_count=1)
        self.channel.queue_declare(
            queue=self.queue_name, callback=self.on_queue_declared
        )

    def on_queue_declared(self, method_frame):
        logger.info("Queue declared")
        if self.channel:
            self.channel.basic_consume(
                queue=self.queue_name, on_message_callback=self.on_message
            )

    def on_message(self, channel, method, properties, body):
        logger.info(f"Received message: {body.decode()}")
        loop = asyncio.get_event_loop()
        asyncio.run_coroutine_threadsafe(
            self.on_message_async(channel, method, properties, body), loop
        )
