import logging

from logging import Logger
from typing import Tuple


def _cli_options(verbosity: int) -> Tuple[int, str]:
    fmt = '%(message)s'
    level = logging.WARN

    if verbosity == 1:
        level = logging.INFO

        urllib3 = logging.getLogger("urllib3")
        urllib3.setLevel(logging.DEBUG)

    if verbosity == 2:
        level = logging.DEBUG

        botocore = logging.getLogger("botocore")
        botocore.setLevel(logging.INFO)

        botocore = logging.getLogger("botocore.endpoint")
        botocore.setLevel(logging.DEBUG)

    if verbosity == 3:
        fmt = '%(name)s %(message)s'
        level = logging.NOTSET

    if verbosity > 3:
        fmt = '%(filename)s:%(lineno)d:%(name)s:%(message)s'
        level = logging.NOTSET

    return level, fmt


def configConsoleLogger(verbosity: int) -> None:
    level, fmt = _cli_options(verbosity)
    logging.basicConfig(format=fmt)

    root = logging.getLogger()
    root.setLevel(level)

    _commonLogger()
    return


def configFileLogger(fname: str, level: int) -> Logger:
    _commonLogger()

    logger = logging.getLogger()
    logger.setLevel(level)

    logFormatter = logging.Formatter(
        '%(asctime)s:%(levelname)s:%(message)s'
    )
    fileHandler = logging.FileHandler(fname)
    fileHandler.setFormatter(logFormatter)
    # fileHandler.setLevel(level)
    logger.addHandler(fileHandler)

    return logger


def _commonLogger() -> None:
    requests_log = logging.getLogger("urllib3")
    requests_log.propagate = True
