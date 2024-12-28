import json
import ftplib
import os
import logging
from utils.config import config

logger = logging.getLogger(__name__)


class TableUploader:
    def __init__(self):
        self.session = None

    def start(self):
        # Read credentials from file
        logger.info(f"Authenticating to FTP...")
        self.session = ftplib.FTP(
            config["CRED_FTP"]["server"],
            config["CRED_FTP"]["username"],
            config["CRED_FTP"]["password"],
        )
        logger.info("Done authenticating to FTP")

    def upload(self, table_params, local_dir):
        file_name = table_params["output_file"]
        logger.info(f"Uploading file: {file_name}")
        src_file = os.path.join(local_dir, file_name)
        dst_file = os.path.basename(table_params["remote_file"])
        dst_path = os.path.dirname(table_params["remote_file"])
        self.session.cwd(dst_path)
        self.session.storbinary("STOR " + dst_file, open(src_file, "rb"))
        logger.info(f"Uploaded file: {file_name}")

    def quit(self):
        logger.info("Disconnecting from FTP...")
        self.session.quit()
        logger.info("Disconnected from FTP")
