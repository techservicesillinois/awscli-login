from argparse import Namespace
from functools import wraps
from multiprocessing import Process, Pipe
from os import walk, sep
from os.path import basename, getmtime
from sys import exc_info
from time import sleep
from typing import Callable
from unittest.mock import patch

# This module allows a traceback to be pickled!
from tblib import pickling_support

from awscli.clidriver import main

from awscli_login.util import (
    file2bytes,
)


def fork():
    """A decorator for running a function in a separate forked process.

    This is particularly useful for running unittests in a separate
    process were a strong degree of isolation is needed. Exceptions
    from the subprocess are captured and reraised in the decorator
    so that unittests will function as expected.

    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            parent, child = Pipe()

            def error_handler(conn, func, *args, **kwargs):
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    pickling_support.install()
                    etype, exp, tb = exc_info()
                    conn.send((etype, str(exp), tb))
                    exit(1)
                finally:
                    conn.close()

            p = Process(
                target=error_handler,
                args=(child, func, *args),
                kwargs=kwargs,
            )
            p.start()
            p.join()

            if p.exitcode == 1:
                etype, message, tb = parent.recv()
                raise Exception(str(etype) + ': ' + message).with_traceback(tb)
            return
        return wrapper
    return decorator


def login_cli_args(
    ask_password=False,
    ecp_endpoint_url=None,
    factor=None,
    force_refresh=False,
    passcode=None,
    password=None,
    refresh=0,
    role_arn=None,
    subcommand=None,  # TODO FIXME!?
    username=None,
    verbose=0,
) -> Namespace:
    """
    Function for mocking cli args to login.
    """
    return Namespace(**locals())


def configure_cli_args(
    verbose=0,
) -> Namespace:
    """
    Function for mocking cli args to login.
    """
    return Namespace(**locals())


def exec_awscli(*argv: str) -> None:
    """ Run the aws cli. """
    @patch('sys.argv', ['aws', *argv])
    def run_main():
        main()

    run_main()


# Based on code from:
# https://stackoverflow.com/questions/9727673/list-directory-tree-structure-in-python
def tree(startpath):
    r = ''

    for root, dirs, files in walk(startpath):
        level = root.replace(startpath, '').count(sep)
        indent = ' ' * 4 * (level)
        r += '{}{}/\n'.format(indent, basename(root))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            r += '{}{}\n'.format(subindent, f)

    return r


def isFileChangedBy(filename: str, func: Callable,
                    *args, **kwargs) -> bool:
    """Tests if a file is changed by a function call.

    Args:
        filename: The file to test.
        func: The function to call
        *args: positional arguments to pass to `func`.
        **kwargs: keyword arguments to pass to `func`.

    Returns:
        True if the file was changed, False otherwise.
    """

    before = file2bytes(filename)
    func(*args, **kwargs)
    after = file2bytes(filename)

    return not (before == after)


def isFileTouchedBy(filename: str, func: Callable,
                    *args, **kwargs) -> bool:
    """Tests if a file is toched by a function call.

    Args:
        filename: The file to test.
        func: The function to call
        *args: positional arguments to pass to `func`.
        **kwargs: keyword arguments to pass to `func`.

    Returns:
        True if the file was touched, False otherwise.
    """
    sleep(1)  # Must sleep or before == after!

    before = getmtime(filename)
    func(*args, **kwargs)
    after = getmtime(filename)

    return not bool(after - before)
