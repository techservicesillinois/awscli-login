""" This module is used to process ~/.aws-login/config """
import logging
import sys
import traceback

from argparse import Namespace
from collections import OrderedDict
from configparser import ConfigParser, SectionProxy
from datetime import datetime
from functools import wraps
from getpass import getuser, getpass
from os import environ, makedirs, path
from os.path import expanduser
from pathlib import Path
from typing import Any, Dict, FrozenSet, Optional
from urllib.parse import urlparse

try:
    from awscli.customizations.configure.writer import ConfigFileWriter
except ImportError:  # pragma: no cover
    pass

try:
    from botocore.session import Session
except ImportError:  # pragma: no cover
    class Session():  # type: ignore
        pass

try:
    from keyring import get_password, set_password
except ImportError:  # pragma: no cover
    pass

from .const import (
    DUO_HEADER_FACTOR,
    DUO_HEADER_PASSCODE,
)
from .exceptions import (
    AWSCLILogin,
    AlreadyLoggedIn,
    AlreadyLoggedOut,
    ExistingTape,
    InvalidFactor,
    MissingTape,
    ProfileMissingArgs,
    ProfileNotFound,
    VcrFailedToLoad,
)
from .logger import configConsoleLogger
from .util import secure_touch, config_vcr
from ._typing import Creds, Role

CONFIG_DIR = '.aws-login'
CONFIG_FILE = path.join(CONFIG_DIR, 'config')
JAR_DIR = path.join(CONFIG_DIR, 'cookies')
CREDENTIALS_FILE = path.join(CONFIG_DIR, 'credentials')

ERROR_NONE = 0
ERROR_UNKNOWN = 1

FACTORS = ['auto', 'push', 'passcode', 'sms', 'phone']
DISABLE = ["0", "no", "false", "off", "disable"]

logger = logging.getLogger(__name__)


class Profile:
    """
    This class reads the current login profile from ~/.aws-login/config
    """
    # Public vars
    name: str  # Profile name

    # Required args from profile
    ecp_endpoint_url: str

    # Optional args from profile
    username: str
    password: str
    role_arn: str
    enable_keyring: bool = False
    factor: Optional[str]
    passcode: str
    force_refresh: bool = False
    duration: int = 0
    http_header_factor: str
    http_header_passcode: str
    verify_ssl_certificate: bool = True

    # path to profile configuration file
    config_file: str
    credentials_file: str

    # Private vars
    _credentials_obj: ConfigParser
    _profile_credentials: Optional[SectionProxy]

    _args: Optional[Namespace] = None
    _required: FrozenSet[str] = frozenset(['ecp_endpoint_url'])
    _optional: Dict[str, Any] = {
            'username': None,
            'password': None,
            'role_arn': None,
            'enable_keyring': False,
            'factor': None,
            'passcode': None,
            'duration': 0,  # duration can't be less than 900, btw
            'http_header_factor': None,
            'http_header_passcode': None,
            'verify_ssl_certificate': True,
    }

    _cli_only: Dict[str, Any] = {
            'force_refresh': False,
    }

    _config_options: Dict[str, str] = OrderedDict(
        [
            ('ecp_endpoint_url', 'ECP Endpoint URL'),
            ('username', 'Username'),
            ('enable_keyring', 'Enable Keyring'),
            ('factor', 'Duo Factor'),
            ('role_arn', 'Role ARN'),
        ]
    )

    # Extra override args from command line
    _override: Dict[str, str] = {
        'enable_keyring': 'ask_password',
    }

    def _init_dir(self) -> None:
        """ Create ~/.aws-login directory if it does not exist. """
        root = environ.get('AWSCLI_LOGIN_ROOT')

        self.home = root if root is not None else expanduser('~')
        self.config_file = path.join(self.home, CONFIG_FILE)
        self.credentials_file = path.join(self.home, CREDENTIALS_FILE)

        makedirs(path.join(self.home, CONFIG_DIR), mode=0o700, exist_ok=True)
        makedirs(path.join(self.home, JAR_DIR), mode=0o700, exist_ok=True)

    def _set_attrs(self, validate: bool) -> None:
        """ Load login profile from configuration. """
        config = ConfigParser()
        config.read(self.config_file)
        logger.info("Loaded config file: " + self.config_file)

        # Requried configuration
        self._set_req_attrs(config, validate)

        # Optional configuration
        self._set_opt_attrs(config, validate)

        # Warn if unknown attributes are found
        self._warn_on_unknown_attrs(config, validate)

    def _set_attrs_from_args(self) -> None:
        """ Load command line options. """
        self.options = self._required | frozenset(self._optional.keys()) \
            | frozenset(self._cli_only.keys())
        options = self.options - frozenset(self._override.keys())

        for option in options:
            value = getattr(self._args, option)

            # Allow False, empty strings, zero, etc.
            if value is not None:
                setattr(self, option, value)

                # Set factor to passcode if a passcode is given #117
                if option == 'passcode':
                    self.factor = 'passcode'

    def _set_override_attrs(self) -> None:
        """ Disable attrs if overriden on command line. """
        for attr, option in self._override.items():
            value = getattr(self._args, option)

            if value:
                setattr(self, attr, False)

    def __init__(self, session: Session, args: Optional[Namespace],
                 validate: bool = True) -> None:
        """Load login profile.

        Args:
            session: a botocore session used to determine the current profile.
            args: an object containing command line arguments.
            validate: if true will validate the profile.

        Raises:
            ProfileNotFound: If the Profile can not be found.
            ProfileMissingArgs: If required arguments are missing.
        """
        self.name = session.profile if session.profile else 'default'
        self._args = args

        self._init_dir()
        self.reload(validate)

        logger.info("Loaded login profile: " + self.name)

    def __getattr__(self, item):
        """ Process dynamic attributes. """
        if item == 'cookies':
            if self.username:
                filename = self.username + '.txt'
                return path.join(self.home, JAR_DIR, filename)
            else:
                return None
        else:
            mesg = "'%s' object has no attribute '%s'"
            raise AttributeError(mesg % (self.__class__.__name__, item))

    def __dir__(self):
        """ Allows dir to work with dynamic attributes. """
        return super().__dir__() + ['cookies']

    def raise_if_logged_in(self) -> None:
        """ Throws an exception if already logged in. """
        profile = self._profile_credentials

        # A user is NOT logged in if credentials are expired or nonexistent
        if profile is None or self.are_credentials_expired():
            return

        if 'aws_role_arn' in profile and profile['aws_role_arn'] != '':
            raise AlreadyLoggedIn

    def raise_if_logged_out(self) -> None:
        """ Throws an exception if already logged out. """
        profile = self._profile_credentials

        # A user is NOT logged in if credentials can not be refreshed
        if profile is None or 'aws_role_arn' not in profile or \
           profile['aws_role_arn'] == '':
            raise AlreadyLoggedOut

    def _get_profile(self, config: ConfigParser,
                     validate: bool) -> Optional[SectionProxy]:
        """ Helper function for grabing a profile. """
        if self.name not in config:
            if validate:
                raise ProfileNotFound(self.name)

            return None

        return config[self.name]

    def _set_req_attrs(self, config: ConfigParser, validate: bool) -> None:
        """ Load required args from profile [~/.aws-login/config]. """
        errors = []
        section = self._get_profile(config, validate)

        for attr in self._required:
            try:
                if validate and section is not None:
                    setattr(self, attr, section[attr])
                elif section is not None:
                    setattr(self, attr, section.get(attr))
                else:
                    setattr(self, attr, None)
            except KeyError:
                errors.append(attr)
        if errors:
            raise ProfileMissingArgs(self.name, *errors)

    def _set_opt_attrs(self, config: ConfigParser, validate: bool) -> None:
        """ Load optional args from profile [~/.aws-login/config]. """
        value: Any = None
        section = self._get_profile(config, validate)

        for attr, default in self._optional.items():
            # section.get(attr) will always be a string
            # because ConfigParser treats everything as
            # a string
            if section is not None:
                value = section.get(attr, default)

                # Type cast string to correct type
                # based on the default value
                if value != default:
                    if type(default) is bool:
                        value = section.getboolean(attr)
                    elif type(default) is int:
                        value = int(value)
            else:
                value = default

            setattr(self, attr, value)

    def _warn_on_unknown_attrs(self, config: ConfigParser,
                               validate: bool) -> None:
        """ Load required args from profile [~/.aws-login/config]. """
        section = self._get_profile(config, validate)

        if section:
            for attr in section:
                if attr not in self._required and attr not in self._optional:
                    logger.warning('Unknown attribute "' + attr + '" in ' +
                                   self.name + ' profile ')

    def is_factor_valid(self):
        """ Return True if self.factor is valid. False otherwise. """
        return self.factor in FACTORS

    def raise_if_factor_invalid(self):
        """ Raise exception if self.factor is invalid. """
        if self.factor and not self.is_factor_valid():
            raise InvalidFactor(self.factor)

    def is_factor_prompt_disabled(self) -> bool:
        if self.factor:
            return self.factor.lower() in DISABLE or self.is_factor_valid()
        else:
            return False

    def get_username(self):
        """ Get username from user if necessary. """
        if self.username is None:
            username = getuser()
            self.username = input("Username [%s]: " % username) or username

    def get_password(self):
        """ Get password from user if necessary. """
        if self.enable_keyring:
            if self.password is not None:
                logger.warning('Using keyring: Ignoring password set via'
                               ' configuration file or command line.')

            ukey = self.username + '@' + urlparse(self.ecp_endpoint_url).netloc
            self.password = get_password("awscli_login", ukey)

        if self.password is None:
            self.password = getpass()

        if self.enable_keyring:
            set_password("awscli_login", ukey, self.password)

    # Can we make this DRYer?
    def get_credentials(self, first_pass: bool = True) -> Creds:
        """ Get credentials from user if necessary. """
        self.get_username()
        self.get_password()

        # TODO add support for any factor...
        # https://github.com/JohnPfeifer/duo-non-browser/wiki
        # https://duo.com/docs/authapi#/auth
        headers = {}
        if not self.is_factor_prompt_disabled():
            self.factor = input('Factor: ') or None
            self.raise_if_factor_invalid()

        if self.is_factor_valid():
            assert isinstance(self.factor, str), "Factor is not a string!"

            if self.http_header_factor is not None:
                headers[self.http_header_factor] = self.factor
            else:
                headers['X-Shiboleth-Duo-Factor'] = self.factor
                headers[DUO_HEADER_FACTOR] = self.factor

            if not first_pass or self.factor == 'passcode':
                if self.passcode is None:
                    code = input('Code: ')
                else:
                    code = self.passcode

                if self.http_header_passcode is not None:
                    headers[self.http_header_passcode] = code
                else:
                    headers['X-Shiboleth-Duo-Passcode'] = code
                    headers[DUO_HEADER_PASSCODE] = code

        return self.username, self.password, headers

    # TODO Add validation...
    def update(self) -> None:
        """ Interactively update the profile. """
        new_values = {}
        writer = ConfigFileWriter()

        for attr, string in self._config_options.items():
            value = getattr(self, attr, self._optional.get(attr))

            prompt = "%s [%s]: " % (string, value)
            value = input(prompt)

            if value:
                new_values[attr] = value

        if new_values:
            if self.name != 'default':
                new_values['__section__'] = self.name

            secure_touch(self.config_file)
            writer.update_config(new_values, self.config_file)

    def reload(self, validate: bool = True):
        """ Reloads profile from disk [~/.aws-login/config]. """
        self._set_attrs(validate)

        if self._args:
            self._set_attrs_from_args()
            self._set_override_attrs()

        self._set_attrs_from_credentials_file()

    def are_credentials_expired(self) -> bool:
        """ Return True if credentials are expired. """
        creds = self._profile_credentials
        if creds is None:
            return True

        try:
            expiration = datetime.fromisoformat(creds['expiration'])
            if expiration > datetime.now(tz=expiration.tzinfo):
                return False
        except (ValueError, TypeError, KeyError) as e:
            logger.debug(f"Invalid or missing credentials: {e}")
        return True

    def load_credentials(self) -> Optional[Dict]:
        """ Returns credentials token, None if missing or incomplete."""
        profile = self._profile_credentials
        if profile is None:
            return None

        try:
            return {
                'Credentials': {
                    'AccessKeyId': profile['aws_access_key_id'],
                    'SecretAccessKey': profile['aws_secret_access_key'],
                    'SessionToken': profile['aws_session_token'],
                    'Expiration': datetime.fromisoformat(
                        profile['expiration']),
                }
            }
        except (KeyError, TypeError, ValueError):
            return None

    def _write_credentials_obj(self, message: str):
        """ Write _credentials_obj to ~/.aws-login/credentials. """
        with open(self.credentials_file, 'w') as configfile:
            self._credentials_obj.write(configfile)
            logger.info(message)

    def remove_all_credentials(self) -> None:
        """ Remove all Amazon tokens & roles in ~/.aws-login/credentials. """
        self._credentials_obj = ConfigParser()
        self._write_credentials_obj(
           "Removed temporary STS credentials for all profiles.")

    def remove_credentials(self) -> bool:
        """ Remove Amazon token and role in ~/.aws-login/credentials. """
        status = self._credentials_obj.remove_section(self.name)
        self._write_credentials_obj(
            f"Removed temporary STS credentials from profile: {self.name}")
        return status

    def save_credentials(self, token: Dict, role: Role):
        """ Caches an Amazon token and role in ~/.aws-login/credentials. """
        config = self._credentials_obj
        profile = self._profile_credentials
        creds = token['Credentials']

        if profile is None:
            config.add_section(self.name)
            profile = config[self.name]
            self._profile_credentials = profile

        profile['aws_access_key_id'] = creds['AccessKeyId']
        profile['aws_secret_access_key'] = creds['SecretAccessKey']
        profile['aws_session_token'] = creds['SessionToken']
        profile['aws_security_token'] = creds['SessionToken']
        try:
            profile['expiration'] = creds['Expiration'].isoformat()
        except AttributeError:
            profile['expiration'] = creds['Expiration']
        profile['aws_principal_arn'] = role[0]
        profile['aws_role_arn'] = role[1]
        profile['username'] = self.username

        self._write_credentials_obj(
            "Saved temporary STS credentials to profile: {self.name}")

    def _set_attrs_from_credentials_file(self):
        """ Load username and role from credentials file. """
        config = ConfigParser()
        config.read(self.credentials_file)
        self._credentials_obj = config

        if config.has_section(self.name):
            profile = config[self.name]
            if self.role_arn is None:
                self.role_arn = profile.get('aws_role_arn')
            if self.username is None:
                self.username = profile.get('username')
        else:
            profile = None

        self._profile_credentials = profile


def _error_handler(Profile, skip_args=True, validate=False,
                   extra_args_handler=None):
    """ Helper function to generate a logging & exception decorator. """
    def decorator(f):
        @wraps(f)
        def wrapper(args: Namespace, session: Session):
            exp: Optional[Exception] = None
            exc_info = None
            code = ERROR_NONE
            sig = None
            fargs = (extra_args_handler(args), ) if extra_args_handler else ()

            try:
                if not skip_args:
                    # verbosity can only be set at command line
                    configConsoleLogger(args.verbose)
                    del args.verbose

                    filename, load = config_vcr(args)
                    profile = Profile(session, args, validate)
                else:
                    filename, load = (None, None)
                    profile = Profile(session, None, validate)
                fargs = (profile, session) + fargs

                if load is not None and filename is not None:
                    try:
                        from vcr import VCR
                        vcr = VCR(record_mode='none' if load else 'all')

                        path = Path(filename)
                        if load and not path.is_file():
                            raise MissingTape(filename)
                        if not load and path.exists():
                            raise ExistingTape(filename)

                        # 169.254.169.254 is the AWS EC2 instance metadata
                        # service. Botocore always attempts to connect. It
                        # should recieve a timeout, but vcrpy cassettes can
                        # not record timeouts so we need to add the instance
                        # metadata service to the ignore_hosts field so the
                        # the request timeout is allowed to happen.
                        #
                        # NOTA BENE: Cassettes that return an empty response
                        # for 169.254.169.254 cause botocore to crash.
                        vcr_args = {"ignore_hosts": ('169.254.169.254', )}
                        with vcr.use_cassette(filename, **vcr_args):
                            f(*fargs)
                    except ModuleNotFoundError:
                        raise VcrFailedToLoad
                else:
                    f(*fargs)
            except AWSCLILogin as e:
                exc_info = sys.exc_info()
                code = e.code
                exp = e
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


def error_handler(skip_args=True, validate=False, extra_args_handler=None):
    """ A decorator for exception handling and logging. """
    return _error_handler(Profile, skip_args, validate, extra_args_handler)
