import os
import logging
import logging.handlers

FILE = os.path.join("log", "default.log")
LEVEL = "INFO"
FORMAT = (
    "%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s"
)
BACKUP_COUNT = 14


# Setup logging
def setup_logger(name: str = __name__, file: str = FILE, level: str = LEVEL):
    logging.basicConfig(
        level=level,
        format=FORMAT,
        handlers=[
            logging.StreamHandler(),  # write logs to console
            logging.handlers.TimedRotatingFileHandler(  # write logs to file
                file, when="midnight", backupCount=BACKUP_COUNT
            ),
        ],
    )
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)
    logging.getLogger("oauth2client").setLevel(logging.WARNING)
    logging.getLogger("pika").setLevel(logging.WARNING)
    logger = logging.getLogger(name)
    return logger
