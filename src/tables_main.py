import json
import os
import pika
from utils import table_converter
from utils import table_uploader
from utils.config import config
from utils.config import tables
from utils.log import setup_logger

# Setup logging
logger = setup_logger(
    name=__name__,
    file=config["LOG"]["NOTIFIER"]["FILE"],
    level=config["LOG"]["NOTIFIER"]["LEVEL"],
)


# Get output file path
def get_output_file_path(file_name):
    return os.path.join(config["OUTPUT"]["DIR"], file_name)


# Convert one table from Google Spreadsheet to JavaScript (JSON)
def convert_table(converter, table_params):
    logger.info(f"Table name: {table_params['generator_name']}")
    output_file = get_output_file_path(table_params["output_file"])
    converter.setSpreadsheetId(table_params["spreadsheetId"])
    converter.setSpreadsheetRange(table_params["range"])
    converter.readTable()
    converter.parseData(table_params["fields"])
    converter.saveToFile(output_file)
    logger.info(f"Done table: {table_params['generator_name']}")


# Upload generated JavaScript file to FTP
def upload_table(uploader, table_params):
    logger.info(f"Uploading file: {table_params['output_file']}")
    uploader.upload(table_params, local_dir=config["OUTPUT"]["DIR"])
    logger.info(f"Uploaded file: {table_params['output_file']}")


# Publish results to RabbitMQ
def publish_result(msg):
    logger.info("Publishing result...")
    message_json = json.dumps(msg)
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()
    channel.queue_declare(queue=config["RABBITMQ"]["QUEUES"]["RESULTS"])
    channel.basic_publish(
        exchange="",
        routing_key=config["RABBITMQ"]["QUEUES"]["RESULTS"],
        body=message_json,
    )
    connection.close()
    logger.info("Done publishing result!")


# Handle new task from RabbitMQ
def on_new_task_message(ch, method, properties, body):
    logger.info("Got new task...")
    try:
        # Decode incoming message
        msg = json.loads(body.decode())
        msg_job = msg.get("job", "no_job")
    except:
        logger.warning(
            f"Error decoding incoming message: {body.decode()}", exc_info=True
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return
    # Prepare converter and uploader
    logger.info(f"Prepare job '{msg_job}'...")
    converter = table_converter.TableConverter()
    uploader = table_uploader.TableUploader()
    converter.auth()
    uploader.start()
    for table_params in tables:
        # Convert and upload one table
        if msg_job not in [table_params.get("generator_name"), "all"]:
            logger.info(f"Skipping table {table_params['generator_name']}")
            continue
        logger.info(f"Processing table {table_params['generator_name']}...")
        convert_table(converter, table_params)
        upload_table(uploader, table_params)
        # Publish result
        msg["uuid"] = msg.get("uuid", "no_uuid")
        msg["table"] = table_params["generator_name"]
        msg["result"] = "done"
        publish_result(msg)
        logger.info(f"Done table {table_params['generator_name']}!")
    uploader.quit()
    ch.basic_ack(delivery_tag=method.delivery_tag)
    logger.info("Done converting!")


# MAIN
def main():
    logger.info(f"Starting table converter with PID={os.getpid()}...")
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
    logger.info("Finished 'FST-OTM table converter' worker!")


# Entry point
if __name__ == "__main__":
    main()
