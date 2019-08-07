import os
import logging
import configparser

from datetime import datetime, timezone
from os import path
from time import sleep
from typing import Dict, List, Tuple

from awscli.customizations.configure.set import ConfigureSetCommand
from botocore.session import Session

from .const import ERROR_INVALID_PROFILE_ROLE
from .exceptions import SAML
from .typing import Role

## WHY CAN'T I IMPORT util or __main__ ??
awsconfigfile = path.join('.aws', 'credentials')
accountsfile = path.join(
                         os.path.expanduser("~"),
                         '.aws-login',
                         'accounts.ini'
                        )

identityfile = path.join(
                         os.path.expanduser("~"),
                         '.aws-login',
                         'identity.txt'
                        )
def read_account_names_file():
    account_names = {}
    if os.path.exists(accountsfile):
        config = configparser.ConfigParser()
        config.read(accountsfile)
        for key in config['ACCOUNT_NAMES']:
            account_names[key] = config['ACCOUNT_NAMES'][key]
    return account_names


def write_identity_file(account_id):
    account_names = read_account_names_file()
    with open(identityfile,'w') as f:
        print(account_names[account_id], file=f)

logger = logging.getLogger(__name__)

TRUE = ("yes", "true", "t", "1")
FALSE = ("no", "false", "f", "0")


def sort_roles(role_arns: List[Role]) \
               -> List[Tuple[str, List[Tuple[int, str]]]]:
    """ TODO """
    accounts = {}  # type: Dict[str, List[Tuple[int, str]]]
    r = []  # type: List[Tuple[str, List[Tuple[int, str]]]]

    for index, arn in enumerate(role_arns):
        acct = arn[1].split(':')[4]  # type: str
        role = arn[1].split(':')[5].split('/')[1]  # type: str

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
    select = {}  # type: Dict[int, int]

    # Return profile_role if valid and set
    if profile_role is not None:
        pr = [(idp, role) for idp, role in role_arns if role == profile_role]
        if pr:
            return pr[0]
        else:
            logger.error(ERROR_INVALID_PROFILE_ROLE % profile_role)

    if n > 1:
        print("Please choose the role you would like to assume:")
        account_names = read_account_names_file()

        accounts = sort_roles(role_arns)
        for acct, roles in accounts:
            if acct in account_names:
                print(
                        ' ' * 4,
                        "Account: %s (%s)" % (account_names[acct], acct)
                     )
            else:
                print(' ' * 4, "Account:", acct)

            for index, role in roles:
                print(' ' * 8, "[ %d ]:" % i, role)
                select[i] = index
                i += 1

        print("Selection:\a ", end='')
# TODO need error checking
        return role_arns[select[int(input())]]
    elif n == 1:
        return role_arns[0]
    else:
        raise SAML("No roles returned!")


class Args:
    """ A stub class for passing arguments to ConfigureSetCommand """
    def __init__(self, varname: str, value: str) -> None:
        self.varname = varname
        self.value = value


def _aws_set(session: Session, varname: str, value: str) -> None:
    """
    This is a helper function for save_credentials.

    The function is the same as running:

    $ aws configure set varname value
    """
    set_command = ConfigureSetCommand(session)
    set_command._run_main(Args(varname, value), parsed_globals=None)


def remove_credentials(session: Session) -> None:
    """
    Removes current profile's credentials from ~/.aws/credentials.
    """

    ConfigureSetCommand._WRITE_TO_CREDS_FILE.append("aws_security_token")
    profile = session.profile if session.profile else 'default'

    _aws_set(session, 'aws_access_key_id', '')
    _aws_set(session, 'aws_secret_access_key', '')
    _aws_set(session, 'aws_session_token',  '')
    _aws_set(session, 'aws_security_token', '')
    logger.info("Removed temporary STS credentials from profile: " + profile)

def remove_identity_file():
    os.remove(identityfile)

def save_credentials(session: Session, token: Dict) -> datetime:
    """ Takes an Amazon token and stores it in ~/.aws/credentials """

    ConfigureSetCommand._WRITE_TO_CREDS_FILE.append("aws_security_token")

    creds = token['Credentials']
    profile = session.profile if session.profile else 'default'

    _aws_set(session, 'aws_access_key_id', creds['AccessKeyId'])
    _aws_set(session, 'aws_secret_access_key', creds['SecretAccessKey'])
    _aws_set(session, 'aws_session_token',  creds['SessionToken'])
    _aws_set(session, 'aws_security_token',  creds['SessionToken'])
    logger.info("Saved temporary STS credentials to profile: " + profile)

    assert isinstance(creds['Expiration'], datetime), \
        "Amazon returned bad Expiration!"
    return creds['Expiration']


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


def nap(expires: datetime, percent: float) -> None:
    """TODO. """
    tz = timezone.utc
    ttl = int((expires - datetime.now(tz)).total_seconds())
    sleep_for = ttl * 0.9

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
    os.fchmod(fd, 0o600)
    os.close(fd)
