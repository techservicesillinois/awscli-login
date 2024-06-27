import logging
import os

from argparse import Namespace
from shutil import which
from typing import Any, Dict, List, Optional, Tuple

try:
    from awscli.customizations.configure.set import ConfigureSetCommand
except ImportError:  # pragma: no cover
    pass

try:
    from awscli.customizations.configure.get import ConfigureGetCommand
except ImportError:  # pragma: no cover
    pass

try:
    from botocore.session import Session
except ImportError:  # pragma: no cover
    class Session:  # type: ignore
        pass

from .const import ERROR_INVALID_PROFILE_ROLE
from .exceptions import (
    ConfigError,
    ConfigurationFailed,
    CredentialProcessMisconfigured,
    CredentialProcessNotSet,
    InvalidSelection,
    SAML,
    TooManyHttpTrafficFlags,
)
from ._typing import Role

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


def get_selection(role_arns: List[Role], profile_role: Optional[str] = None,
                  interactive: bool = True) -> Role:
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
            if not interactive:
                raise ConfigError(ERROR_INVALID_PROFILE_ROLE % profile_role)
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


def config_vcr(args: Namespace) -> Tuple[Optional[str], Optional[bool]]:
    """ Process optional save_http_traffic and load_http_traffic flags. """
    if not hasattr(args, "save_http_traffic"):
        return None, None

    if not hasattr(args, "load_http_traffic"):
        return None, None

    if args.save_http_traffic and args.load_http_traffic:
        raise TooManyHttpTrafficFlags

    filename = None
    load = None

    if args.save_http_traffic:
        filename = args.save_http_traffic
        load = False

    if args.load_http_traffic:
        filename = args.load_http_traffic
        load = True

    del args.save_http_traffic
    del args.load_http_traffic

    return filename, load


def token(access_key_id="", secret_access_key_id="",
          session_token="", expiration="") -> Dict[str, Dict[str, Any]]:
    token = {
        'Credentials': {
            'AccessKeyId': access_key_id,
            'SecretAccessKey': secret_access_key_id,
            'SessionToken': session_token,
            'Expiration': expiration,
        }
    }
    if expiration is None:
        del token['Credentials']['Expiration']
    return token


class Args:
    """ A stub class for passing arguments to ConfigureSetCommand """

    def __init__(self, varname: str, value: str) -> None:
        self.varname = varname
        self.value = value


def _aws_set(session: Session, varname: str, value: str) -> None:
    """ The function is the same as running:

    $ aws configure set varname value
    """
    set_command = ConfigureSetCommand(session)
    set_command._run_main(Args(varname, value), parsed_globals=None)


def _aws_get(session: Session, varname: str) -> str:
    """ The function is the same as running:

    $ aws configure get varname
    """
    get_command = ConfigureGetCommand(session)
    return get_command._get_dotted_config_value(varname)


def _safe_aws_set(session, **kwargs):
    if input('Overwrite to enable login? ').lower() in ['y', 'yes']:
        for k, v in kwargs.items():
            _aws_set(session, k, v)
    else:
        raise ConfigurationFailed


def update_credential_file(session: Session, profile: str):
    """Adds credential_process to ~/.aws/credentials
    file for active profile."""
    key_id = _aws_get(session, 'aws_access_key_id')
    access_key = _aws_get(session, 'aws_secret_access_key')
    session_token = _aws_get(session, 'aws_session_token')

    if key_id or access_key or session_token:
        print(f'WARNING: Profile {profile} contains credentials.')
        _safe_aws_set(session, aws_access_key_id='', aws_secret_access_key='',
                      aws_session_token='')

    cmd = f'aws-login --profile {profile}'
    ConfigureSetCommand._WRITE_TO_CREDS_FILE.append("credential_process")
    current_cmd = _aws_get(session, 'credential_process')
    if not current_cmd:
        _aws_set(session, 'credential_process', cmd)
    elif current_cmd != cmd:
        print(f'WARNING: credential_process set to: {current_cmd}.')
        _safe_aws_set(session, credential_process=cmd)


def raise_if_credential_process_not_set(
        session: Session, profile: str) -> None:
    """ Raises 'CredentialProcessNotSet' if 'credential_process'
        not set for the active profile.
    """
    proc = _aws_get(session, 'credential_process')
    if proc is None:
        raise CredentialProcessNotSet(profile)

    args = proc.split()
    cmd = args[0]

    if not (which(cmd) and cmd.endswith("aws-login")):
        raise CredentialProcessMisconfigured(profile)
    try:
        if not (args[args.index("--profile") + 1] == profile):
            raise CredentialProcessMisconfigured(profile)
    except (ValueError, IndexError):
        raise CredentialProcessMisconfigured(profile)
