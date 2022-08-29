import logging
import os
import sys
import traceback

from argparse import Namespace
from datetime import datetime, timezone
from functools import wraps
from time import sleep
from typing import Dict, List, Optional, Tuple

from botocore.session import Session
from daemoniker import SIGABRT, SIGINT, SIGTERM

from .config import ERROR_NONE, ERROR_UNKNOWN, Profile
from .const import ERROR_INVALID_PROFILE_ROLE
from .exceptions import SAML, AWSCLILogin, InvalidSelection
from .logger import configConsoleLogger
from .typing import Role

logger = logging.getLogger(__name__)


def sort_roles(role_arns: List[Role]) \
               -> List[Tuple[str, List[Tuple[int, str]]]]:
    """ TODO """
    accounts: Dict[str, List[Tuple[int, str]]] = {}
    r: List[Tuple[str, List[Tuple[int, str]]]] = []

    for index, arn in enumerate(role_arns):
        acct: str = arn[1].split(':')[4]
        role: str = arn[1].split(':')[5].split('/')[1]

        role_list = accounts.get(acct, list())
        role_list.append((index, role))
        accounts[acct] = role_list

    for acct in sorted(accounts.keys()):
        accounts[acct].sort(key=lambda x: x[1])
        r.append((acct, accounts[acct]))

    return r


def get_selection(role_arns: List[Role], profile_role: str = None) -> Role:
    """ Interactively prompts the user for a role selection. """
    i = 0
    n = len(role_arns)
    select: Dict[int, int] = {}

    # Return profile_role if valid and set
    if profile_role is not None:
        pr = [(idp, role) for idp, role in role_arns if role == profile_role]
        if pr:
            return pr[0]
        else:
            logger.error(ERROR_INVALID_PROFILE_ROLE % profile_role)

    if n > 1:
        print("Please choose the role you would like to assume:")

        accounts = sort_roles(role_arns)
        for acct, roles in accounts:
            print(' ' * 4, "Account:", acct)

            for index, role in roles:
                print(' ' * 8, "[ %d ]:" % i, role)
                select[i] = index
                i += 1

        print("Selection:\a ", end='')
        try:
            return role_arns[select[int(input())]]
        except (ValueError, KeyError):
            raise InvalidSelection
    elif n == 1:
        return role_arns[0]
    else:
        raise SAML("No roles returned!")


def file2bytes(filename: str) -> bytes:
    """
    Takes a filename and returns a byte string with the content of the file.
    """
    with open(filename, 'rb') as f:
        data = f.read()
    return data


def file2str(filename: str) -> str:
    """ Takes a filename and returns a string with the content of the file. """
    with open(filename, 'r') as f:
        data = f.read()
    return data


def nap(expires: datetime, percent: float, refresh: float = None) -> None:
    """TODO. """
    if refresh:
        sleep_for = refresh
    else:
        tz = timezone.utc
        ttl = int((expires - datetime.now(tz)).total_seconds())
        sleep_for = ttl * percent

    logger.info('Going to sleep for %d seconds.' % sleep_for)
    sleep(sleep_for)


def secure_touch(path):
    """Sets a file's permissions to read/write by owner only.

    Sets the file `path`'s mode to 600. The file `path` is created
    if it does not exist.

    Args:
        path - A path to a file.
    """
    fd = os.open(path, os.O_CREAT | os.O_RDONLY, mode=0o600)
    if hasattr(os, "fchmod"):
        os.fchmod(fd, 0o600)
    os.close(fd)


def _error_handler(Profile, skip_args=True, validate=False):
    """ Helper function to generate a logging & exception decorator. """
    def decorator(f):
        @wraps(f)
        def wrapper(args: Namespace, session: Session):
            exp: Optional[Exception] = None
            exc_info = None
            code = ERROR_NONE
            sig = None

            try:
                # verbosity can only be set at command line
                configConsoleLogger(args.verbose)
                del args.verbose

                if not skip_args:
                    profile = Profile(session, args, validate)
                else:
                    profile = Profile(session, None, validate)

                f(profile, session)
            except AWSCLILogin as e:
                exc_info = sys.exc_info()
                code = e.code
                exp = e
            except SIGINT:
                sig = 'SIGINT'
            except SIGABRT:
                sig = 'SIGABRT'
            except SIGTERM:
                sig = 'SIGTERM'
            except Exception as e:
                exc_info = sys.exc_info()
                code = ERROR_UNKNOWN
                exp = e
            finally:
                if exp:
                    logger.error(str(exp), exc_info=False)

                if exc_info:
                    logger.debug(
                        '\n' + ''.join(traceback.format_exception(*exc_info))
                    )

                if sig:
                    logger.info('Received signal: %s. Shutting down...' % sig)

                return code

        return wrapper
    return decorator


def error_handler(skip_args=True, validate=False):
    """ A decorator for exception handling and logging. """
    return _error_handler(Profile, skip_args, validate)
