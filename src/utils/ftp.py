import ftplib
import os
import logging
from utils.config import config

logger = logging.getLogger(__name__)


class FtpUploader:
    def __init__(self):
        self.session = None

    def start(self):
        # Read credentials from file
        logger.info("Authenticating to FTP...")
        self.session = ftplib.FTP(
            config["FTP"]["server"],
            config["FTP"]["username"],
            config["FTP"]["password"],
        )
        if not self.session:
            logger.error("Failed to authenticate to FTP")
            return
        logger.info("Done authenticating to FTP")

    def upload(self, table_params: dict, local_dir: str) -> None:
        file_name = table_params["output_file"]
        logger.info(f"Uploading file: {file_name}")
        src_file = os.path.join(local_dir, file_name)
        dst_file = table_params["output_file"]
        dst_path = config["FTP"]["target_path"]
        if not self.session:
            return
        self.session.cwd(dst_path)
        self.session.storbinary("STOR " + dst_file, open(src_file, "rb"))
        logger.info(f"Uploaded file: {file_name}")

    def quit(self) -> None:
        logger.info("Disconnecting from FTP...")
        if not self.session:
            return
        self.session.quit()
        logger.info("Disconnected from FTP")
