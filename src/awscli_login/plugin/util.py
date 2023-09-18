import logging

from datetime import datetime
from typing import Dict

from awscli.customizations.configure.set import ConfigureSetCommand
from awscli.customizations.configure.get import ConfigureGetCommand
from botocore.utils import parse_timestamp
from botocore.session import Session

from .config import Profile
from ..util import _error_handler

logger = logging.getLogger(__name__)


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


def _aws_get(session: Session, varname: str) -> str:
    """ The function is the same as running:

    $ aws configure get varname value
    """
    get_command = ConfigureGetCommand(session)
    return get_command._get_dotted_config_value(varname)


def credentials_exist(session: Session) -> bool:
    """ Return True if credentials exist. """
    if _aws_get(session, 'aws_access_key_id'):
        return True

    if _aws_get(session, 'aws_secret_access_key'):
        return True

    return False


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

    return parse_timestamp(creds['Expiration'])


def error_handler(skip_args=True, validate=False):
    """ A decorator for exception handling and logging. """
    return _error_handler(Profile, skip_args, validate)
