import logging
import os

from argparse import Namespace
from configparser import ConfigParser, NoSectionError
from shutil import which
from typing import Any, Dict, List, Optional, Tuple

try:
    from awscli.customizations.configure import SectionNotFoundError
except ImportError:  # pragma: no cover
    pass

try:
    from awscli.customizations.configure.writer import ConfigFileWriter
except ImportError:  # pragma: no cover
    class ConfigFileWriter:  # type: ignore
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

from .const import (
    ERROR_INVALID_CRED_PROC_MISSING_PROFILE_ARG,
    ERROR_INVALID_CRED_PROC_PATH,
    ERROR_INVALID_CRED_PROC_WRONG_PROFILE_ARG,
    ERROR_INVALID_PROFILE_ROLE,
    OVERWRITE_PROFILE,
    WARNING_PROFILE_CONTAINS_CREDS,
    YES,
)
from .exceptions import (
    ConfigError,
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
    # Python 3.13 on Windows supports fchmod. It is kind of broken
    # and not useful here (See issue #234).
    if hasattr(os, "fchmod") and os.name == 'posix':
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


def _aws_get(session: Session, varname: str) -> str:
    """ The function is the same as running:

    $ aws configure get varname
    """
    get_command = ConfigureGetCommand(session)
    return get_command._get_dotted_config_value(varname)


def aws_credentials_file_path(session):
    path = session.get_config_variable("credentials_file")
    return os.path.expanduser(path)


def get_aws_credentials(session, profile):
    config = ConfigParser()
    config.read(aws_credentials_file_path(session))
    try:
        return dict(config.items(profile))
    except NoSectionError:
        return None


class ClearConfigFileWriter(ConfigFileWriter):

    def issection(self, line):
        """Return True if line is a valid INI section header.

            >>> writer.isSection("[default]")
            True
        """
        return self.SECTION_REGEX.search(line) is not None

    def isoption(self, line):
        """Return true if line is a valid INI property.

            >>> writer.isOption("foo = bar")
            True
        """
        return self.OPTION_REGEX.search(line)

    def clear_section(self, filename, section, new_values):
        """ Clear section and append new_values. Create file & section
        if they do not exit. """
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()

            # clear section if it exists
            j = self._find_section_start(lines, section) + 1
            i = j
            for line in lines[j:]:
                if self.issection(line):
                    break

                if self.isoption(line):
                    lines.pop(i)
                else:
                    i += 1

            # append data to start of section
            for key, value in new_values.items():
                lines.insert(j, f"{key} = {value}\n")

            with open(filename, 'w') as f:
                f.write(''.join(lines))
        except (FileNotFoundError, SectionNotFoundError):
            # create file or section as needed then append data to section
            if section != 'default':
                new_values['__section__'] = section

            self.update_config(new_values, filename)


def update_credential_file(session: Session, profile: str):
    """Adds credential_process to ~/.aws/credentials
    file for active profile."""
    writer = ClearConfigFileWriter()
    creds = get_aws_credentials(session, profile)
    new_values = {"credential_process": f'aws-login --profile {profile}'}

    if creds is not None:
        necreds = {k: v for (k, v) in creds.items() if v.strip() != ""}
        keys = ["aws_access_key_id", "aws_secret_access_key",
                "aws_session_token", "aws_security_token"]
        if set(necreds.keys()).intersection(keys):
            logger.warning(WARNING_PROFILE_CONTAINS_CREDS % profile)

        cproc = "credential_process"
        if cproc in necreds and necreds[cproc] == new_values[cproc]:
            del necreds[cproc]  # Ignore correctly set credential_process

        if len(necreds) > 0:  # Prompt usr if nonempty unexpected values exist
            if input(OVERWRITE_PROFILE % profile).lower() not in YES:
                return False

    path = aws_credentials_file_path(session)
    writer.clear_section(path, profile, new_values)
    return True


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

    # On Windows Python 3.12 and 3.13, which() returns None if
    # cmd is not in the system path even if it is a full path to
    # an executable file. Adding an additional os.access check
    # resolves the issue (See issue #233).
    if which(cmd) is None and not os.access(cmd, os.F_OK | os.X_OK):
        logger.error(ERROR_INVALID_CRED_PROC_PATH % proc)
        raise CredentialProcessMisconfigured(profile)
    try:
        if not (args[args.index("--profile") + 1] == profile):
            logger.error(ERROR_INVALID_CRED_PROC_WRONG_PROFILE_ARG %
                         (proc, profile))
            raise CredentialProcessMisconfigured(profile)
    except (ValueError, IndexError):
        logger.error(ERROR_INVALID_CRED_PROC_MISSING_PROFILE_ARG % proc)
        raise CredentialProcessMisconfigured(profile)
