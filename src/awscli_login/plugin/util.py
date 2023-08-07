import logging

from shutil import which

from awscli.customizations.configure.set import ConfigureSetCommand
from awscli.customizations.configure.get import ConfigureGetCommand
from botocore.session import Session

from .config import Profile
from ..exceptions import (
    ConfigurationFailed,
    CredentialProcessMisconfigured,
    CredentialProcessNotSet,
)
from ..util import _error_handler

logger = logging.getLogger(__name__)


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


def credentials_exist(session: Session) -> bool:
    """ Return True if credentials exist. """
    if _aws_get(session, 'aws_access_key_id'):
        return True

    if _aws_get(session, 'aws_secret_access_key'):
        return True

    return False


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


def error_handler(skip_args=True, validate=False):
    """ A decorator for exception handling and logging. """
    return _error_handler(Profile, skip_args, validate)
