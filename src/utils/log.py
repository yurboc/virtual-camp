import os
import logging
import logging.handlers

DEFAULT_FILE = os.path.join("log", "default.log")
DEFAULT_LEVEL = "INFO"
DEFAULT_FORMAT = (
    "%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s"
)
DEFAULT_BACKUP_COUNT = 14


# Setup logging
def setup_logger(log_file: str = DEFAULT_FILE, log_level: str = DEFAULT_LEVEL):
    logging.basicConfig(
        level=log_level,
        format=DEFAULT_FORMAT,
        handlers=[
            logging.StreamHandler(),  # write logs to console
            logging.handlers.TimedRotatingFileHandler(  # write logs to file
                log_file, when="midnight", backupCount=DEFAULT_BACKUP_COUNT
            ),
        ],
    )
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)
    logging.getLogger("oauth2client").setLevel(logging.WARNING)
    logging.getLogger("pika").setLevel(logging.WARNING)
    logger = logging.getLogger(__name__)
    return logger
