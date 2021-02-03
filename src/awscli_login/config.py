""" This module is used to process ~/.aws-login/config """
import logging

from argparse import Namespace
from collections import OrderedDict
from configparser import ConfigParser, SectionProxy
from getpass import getuser, getpass
from os import path, makedirs, unlink
from os.path import expanduser, isfile
from typing import Any, Dict, FrozenSet, Optional  # NOQA
from urllib.parse import urlparse

from awscli.customizations.configure.writer import ConfigFileWriter
from botocore.session import Session
from keyring import get_password, set_password
from psutil import pid_exists

from .const import (
    DUO_HEADER_FACTOR,
    DUO_HEADER_PASSCODE,
)
from .exceptions import (
    AlreadyLoggedIn,
    InvalidFactor,
    ProfileMissingArgs,
    ProfileNotFound,
)
from .typing import Creds
from .util import secure_touch

CONFIG_DIR = '.aws-login'
CONFIG_FILE = path.join(CONFIG_DIR, 'config')
JAR_DIR = path.join(CONFIG_DIR, 'cookies')
LOG_DIR = path.join(CONFIG_DIR, 'log')

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
    name = None  # type: str  # Profile name

    # Required args from profile
    ecp_endpoint_url = None  # type: str

    # Optional args from profile
    username = None  # type: str
    password = None  # type: str
    role_arn = None  # type: str
    enable_keyring = False  # type: bool
    factor = None  # type: Optional[str]
    passcode = None  # type: str
    refresh = 0  # type: int
    force_refresh = False  # type: bool
    duration = 0  # type: int
    disable_refresh = False  # type: bool
    http_header_factor = None  # type: str
    http_header_passcode = None  # type: str

    # path to profile configuration file
    config_file = None  # type: str

    # Private vars
    _args = None  # type: Optional[Namespace]
    _required = frozenset(['ecp_endpoint_url'])  # type: FrozenSet[str]
    _optional = {
            'username': None,
            'password': None,
            'role_arn': None,
            'enable_keyring': False,
            'factor': None,
            'passcode': None,
            'refresh': 0,  # in seconds
            'duration': 0,  # duration can't be less than 900, btw
            'disable_refresh': False,
            'http_header_factor': None,
            'http_header_passcode': None,
    }  # type: Dict[str, Any]

    _cli_only = {
            'force_refresh': False,
    }  # type: Dict[str, Any]

    _config_options = OrderedDict(
        [
            ('ecp_endpoint_url', 'ECP Endpoint URL'),
            ('username', 'Username'),
            ('enable_keyring', 'Enable Keyring'),
            ('factor', 'Duo Factor'),
            ('role_arn', 'Role ARN'),
        ]
    )  # type: Dict[str, str]

    # Extra override args from command line
    _override = {
        'enable_keyring': 'ask_password',
    }  # type: Dict[str, str]

    def _init_dir(self) -> None:
        """ Create ~/.aws-login directory if it does not exist. """
        home = expanduser('~')

        self.home = home
        self.config_file = path.join(self.home, CONFIG_FILE)

        makedirs(path.join(home, CONFIG_DIR), mode=0o700, exist_ok=True)
        makedirs(path.join(home, LOG_DIR), mode=0o700, exist_ok=True)
        makedirs(path.join(home, JAR_DIR), mode=0o700, exist_ok=True)

        self.pidfile = path.join(home, CONFIG_DIR, self.name + '.pid')
        self.logfile = path.join(home, LOG_DIR, self.name + '.log')

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
        if isfile(self.pidfile):
            with open(self.pidfile, 'r') as f:
                pid = int(f.read())

            if pid_exists(pid):
                raise AlreadyLoggedIn
            else:
                unlink(self.pidfile)

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
        value = None  # type: Any
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
                    if type(default) == bool:
                        value = section.getboolean(attr)
                    elif type(default) == int:
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
                    logger.warn('Unknown attribute "' + attr + '" in ' +
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
                logger.warn('Using keyring: Ignoring password set via'
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
