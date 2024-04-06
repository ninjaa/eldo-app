import sys
import traceback
from typing import Type
from logging import Logger


def log_exception(logger: Logger, exc: Type[BaseException]):
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback_details = traceback.extract_tb(exc_traceback)
    filename, line_number, _, _ = traceback_details[-1]
    logger.error(
        f"An exception of type {exc_type} occurred in {filename} at line {line_number}: {str(exc)}")
