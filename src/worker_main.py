import json
import os
import pika
from utils.config import config
from utils.log import setup_logger
from utils.table_worker import TableWorker

# Setup logging
logger = setup_logger(
    name=__name__,
    file=config["LOG"]["WORKER"]["FILE"],
    level=config["LOG"]["WORKER"]["LEVEL"],
)

# Setup Table Generator
table_worker = TableWorker()


# Handle new task from RabbitMQ
def on_new_task_message(ch, method, properties, body):
    logger.info("Got new task...")
    try:
        # Decode incoming message
        msg = json.loads(body.decode())
        job_type = msg.get("job_type", "no_job_type")
    except:
        logger.warning(
            f"Error decoding incoming message: {body.decode()}", exc_info=True
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return
    # Call handler by job type
    logger.info(f"Prepare handler for '{job_type}'...")
    if job_type == "table_generator":
        table_worker.handle_new_task(msg)
    elif job_type == "image_generator":
        pass
    ch.basic_ack(delivery_tag=method.delivery_tag)
    logger.info(f"Done handler for '{job_type}'!")


# MAIN
def main():
    logger.info(f"Starting VirtualCamp worker with PID={os.getpid()}...")
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()
    channel.queue_declare(queue=config["RABBITMQ"]["QUEUES"]["TASKS"])
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue=config["RABBITMQ"]["QUEUES"]["TASKS"],
        on_message_callback=on_new_task_message,
    )
    logger.info("Worker started, waiting for messages...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()
    logger.info("Finished VirtualCamp worker!")


# Entry point
if __name__ == "__main__":
    main()
