# logger.py
import logging
from pythonjsonlogger import jsonlogger


def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    formatter = jsonlogger.JsonFormatter(
        fmt='%(levelname)s %(asctime)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        timestamp=True,
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger
