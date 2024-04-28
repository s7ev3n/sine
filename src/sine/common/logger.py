import logging
from datetime import datetime

from rich.logging import RichHandler

from sine.common.utils import make_dir_if_not_exist

LOGGER_NAME = "sine"
LOGGER_DIR = ".sine/logs"
DATETIME = datetime.now().strftime("%Y-%m-%d-%H-%M")

def get_logger(logger_name: str) -> logging.Logger:
    # https://rich.readthedocs.io/en/latest/reference/logging.html#rich.logging.RichHandler
    # https://rich.readthedocs.io/en/latest/logging.html#handle-exceptions

    # log to console
    rich_handler = RichHandler(
        show_time=False,
        rich_tracebacks=False,
        show_path=True,
        tracebacks_show_locals=False,
    )
    rich_handler.setFormatter(
        logging.Formatter(
            fmt="%(message)s",
            datefmt="[%X]",
        )
    )
    rich_handler.setLevel(logging.INFO)

    # log to file
    make_dir_if_not_exist(LOGGER_DIR)
    file_handler = logging.FileHandler(filename=f"{LOGGER_DIR}/{DATETIME}.log")
    file_handler.setFormatter(
        logging.Formatter(
            fmt="%(levelname)s %(asctime)s [%(filename)s:%(funcName)s:%(lineno)d] %(message)s",
            datefmt="[%X]",
        )
    )
    file_handler.setLevel(logging.DEBUG)

    _logger = logging.getLogger(logger_name)
    _logger.addHandler(rich_handler)
    _logger.addHandler(file_handler)
    _logger.setLevel(logging.INFO)
    _logger.propagate = False

    return _logger


logger: logging.Logger = get_logger(LOGGER_NAME)
