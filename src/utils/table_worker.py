import os
import logging
from utils.table_converter import TableConverter
from utils.ftp import FtpUploader
from utils import queue
from utils.config import config, tables

logger = logging.getLogger(__name__)


class TableWorker:
    def __init__(self):
        pass

    # Get output file path
    def get_output_file_path(self, file_name: str) -> str:
        return os.path.join(config["TABLE_CONVERTER"]["OUTPUT_DIR"], file_name)

    # Convert one table from Google Spreadsheet to JavaScript (JSON)
    def convert_table(self, converter: TableConverter, table_params: dict) -> None:
        logger.info(f"Table name: {table_params['generator_name']}")
        output_file = self.get_output_file_path(table_params["output_file"])
        converter.setSpreadsheetId(table_params["spreadsheetId"])
        converter.setSpreadsheetRange(table_params["range"])
        converter.readTable()
        converter.parseData(table_params["fields"])
        converter.saveToFile(output_file)
        logger.info(f"Done table: {table_params['generator_name']}")

    # Upload generated JavaScript file to FTP
    def upload_table(self, uploader: FtpUploader, table_params: dict) -> None:
        logger.info(f"Uploading file: {table_params['output_file']}")
        uploader.upload(table_params, local_dir=config["TABLE_CONVERTER"]["OUTPUT_DIR"])
        logger.info(f"Uploaded file: {table_params['output_file']}")

    # Handle new task from RabbitMQ
    def handle_new_task(self, msg: dict) -> None:
        # Prepare converter and uploader
        msg_job = msg.get("job", "no_job")
        logger.info(f"Prepare job '{msg_job}'...")
        converter = TableConverter()
        uploader = FtpUploader()
        converter.auth()
        uploader.start()
        for table_params in tables:
            # Convert and upload one table
            if msg_job not in [table_params.get("generator_name"), "all"]:
                logger.info(f"Skipping table {table_params['generator_name']}")
                continue
            logger.info(f"Processing table {table_params['generator_name']}...")
            self.convert_table(converter, table_params)
            self.upload_table(uploader, table_params)
            # Publish result
            msg["uuid"] = msg.get("uuid", "no_uuid")
            msg["table"] = table_params["generator_name"]
            msg["result"] = "done"
            queue.publish_result(msg)
            logger.info(f"Done table {table_params['generator_name']}!")
        uploader.quit()
        logger.info("Done converting!")
