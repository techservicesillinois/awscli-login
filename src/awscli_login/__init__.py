# Rudimentary documentation for the aws-cli plugin API can be found
# here: https://github.com/aws/aws-cli/issues/1261
import copy
import json
import logging
import os
import subprocess

from argparse import Namespace
from tempfile import NamedTemporaryFile, TemporaryDirectory

try:
    from awscli.customizations.commands import BasicCommand
except ImportError:  # pragma: no cover
    class BasicCommand():  # type: ignore
        pass

try:
    from botocore.session import Session
except ImportError:  # pragma: no cover
    class Session():  # type: ignore
        pass

from .configure import configure, exit_if_credential_process_not_set

logger = logging.getLogger(__package__)


def awscli_initialize(cli):
    """ Entry point called by awscli """
    cli.register('building-command-table.main', inject_commands)
    cli.register('building-command-table.login', inject_subcommands)


def inject_commands(command_table, session: Session, **kwargs):
    """
    Used to inject top-level commands in the awscli command list.
    """
    command_table['login'] = Login(session)
    command_table['logout'] = Logout(session)


def inject_subcommands(command_table, session: Session, **kwargs):
    """
    Used to inject subcommands into the aws login command list.
    """
    command_table['configure'] = Configure(session)


class ExternalCommand(BasicCommand):
    """
    Used to run subcommands in the external aws-login script.
    """

    def _run_main(self, args: Namespace, parsed_globals):
        with TemporaryDirectory() as tmpdir:
            tmp = NamedTemporaryFile(dir=tmpdir, delete=False)
            tmp.write(bytes(json.dumps(vars(args)), 'utf-8'))
            tmp.close()

            cmd = ["aws-login", f"--{self.NAME}", tmp.name]
            if self._session.profile:
                cmd += ["--profile", self._session.profile]

            environ = os.environ.copy()
            # Restore LD_LIBRARY_PATH to avoid C library conflicts #222 #230
            if "LD_LIBRARY_PATH_ORIG" in environ:
                orig = environ["LD_LIBRARY_PATH_ORIG"]
                environ["LD_LIBRARY_PATH"] = orig
                del environ["LD_LIBRARY_PATH_ORIG"]
            return subprocess.run(cmd, env=environ).returncode


class Login(ExternalCommand):
    NAME = 'login'
    DESCRIPTION = ('is a plugin that manages retrieving and rotating'
                   ' Amazon STS keys using the Shibboleth IdP and Duo'
                   ' for authentication.')
    SYNOPSIS = ('aws login [<Arg> ...]')

    # tests/util.py:login_cli_args defaults must match this table
    ARG_TABLE = [
        # Ordering matches order in docs/readme.rst
        # Basic Properties (can be set interactively)
        {
            'name': 'ecp-endpoint-url',
            'no_paramfile': True,
            'default': None,
            'help_text': 'ECP endpoint URL of the IdP'
        },
        {
            'name': 'username',
            'default': None,
            'help_text': 'Username to use on login to IdP'
        },
        {
            'name': 'password',
            'default': None,
            'help_text': 'Password to use on login to IdP'
        },
        {
            'name': 'factor',
            'default': None,
            'help_text': 'The Duo factor to use on login'
        },
        {
            'name': 'passcode',
            'default': None,
            'help_text': 'A Duo passcode'
        },
        {
            'name': 'role-arn',
            'default': None,
            'help_text': 'The Role ARN to select. '
                         'If the IdP returns a single Role it is autoselected.'
        },
        # Advanced Properties (can NOT be set interactively)
        {
            'name': 'duration',
            'default': None,
            'cli_type_name': 'integer',
            'help_text': 'STS credential lifetime in seconds'
        },
        {
            'name': 'http_header_factor',
            'default': None,
            'help_text': 'HTTP Header to store the user\'s Duo factor'
        },
        {
            'name': 'http_header_passcode',
            'default': None,
            'help_text': 'HTTP Header to store the user\'s Duo passcode'
        },
        {
            'name': 'verify-ssl-certificate',
            'default': None,
            'cli_type_name': 'boolean',
            'help_text': 'Verifies the SSL certificate of the IdP'
        },
        # CLI only
        {
            'name': 'ask-password',
            'action': 'store_true',
            'default': False,
            'help_text': 'Force prompt for password'
        },
        {
            'name': 'force-refresh',
            'action': 'store_true',
            'default': False,
            'help_text': 'Forces a login attempt to the IdP using cookies'
        },
        {
            'name': 'verbose',
            'action': 'count',
            'default': 0,
            'cli_type_name': 'integer',
            'help_text': 'Display verbose output'
        },
        {
            'name': 'debug-info',
            'action': 'store_true',
            'default': False,
            'help_text': 'Display debug information'
        },
        {
            'name': 'save-http-traffic',
            'default': None,
            'help_text': 'Save http traffic to a file for debugging'
        },
        {
            'name': 'load-http-traffic',
            'default': None,
            'help_text': 'Load http traffic from file for debugging'
        },
    ]

    UPDATE = False

    def _run_main(self, args: Namespace, parsed_globals):
        r = exit_if_credential_process_not_set(copy.copy(args), self._session)
        if r:
            return r
        else:
            return super()._run_main(args, self._session)


class Logout(ExternalCommand):
    NAME = 'logout'
    DESCRIPTION = ('''
Log out of selected profile by clearing the profile's credentials
stored in ~/.aws-login/credentials.
''')
    SYNOPSIS = ('aws logout')

    ARG_TABLE = [
        {
            'name': 'all',
            'action': 'store_true',
            'default': False,
            'help_text': 'Log out of all profiles',
        },
        {
            'name': 'verbose',
            'action': 'count',
            'default': 0,
            'cli_type_name': 'integer',
            'help_text': 'Display verbose output',
        },
    ]

    UPDATE = False


class Configure(BasicCommand):
    NAME = 'login'
    DESCRIPTION = ('''
Configure LOGIN options. If this command is run with no arguments,
you will be prompted for configuration values such as your IdP's
entity ID and its ECP endpoint URL. You can configure a named profile
using the --profile argument. If your config file does not exist
(the default location is ~/.aws-login/config), it will be created
for you. To keep an existing value, hit enter when prompted for the
value. When you are prompted for information, the current value
will be displayed in [brackets]. If the config item has no value,
it be displayed as [None].

=======================
Configuration Variables
=======================

The following configuration variables are supported in the config
file:

* **ecp_endpoint_url** - The ECP endpoint URL of the IDP to use for AuthN
* **username** - The username to use on login to the IdP.
* **password** - The password to use on login to the IdP.
* **factor** - The Duo factor to use for 2FA
* **passcode** - A Duo passcode
* **role_arn** - The role ARN to select
* **enable_keyring** - If enabled retrieve password from keyring
* **duration** - Time in seconds credentials are valid
* **http_header_factor** - HTTP Header to store Duo factor
* **http_header_passcode** - HTTP Header to store passcode
* **verify_ssl_certificate** - Set to False to skip check of IdP SSL cert
''')
    SYNOPSIS = ('aws login configure')

    ARG_TABLE = [
        {
            'name': 'verbose',
            'action': 'count',
            'default': 0,
            'cli_type_name': 'integer',
            'help_text': 'Display verbose output'
        },
    ]

    UPDATE = False

    EXAMPLES = ('''
To create a new configuration::\n
\n
    $ aws login configure
    Entity ID [None]: urn:mace:incommon:idp.edu
    ECP Endpoint URL [None]: https://idp.edu/idp/profile/SAML2/SOAP/ECP\n
\n
To update just the entity ID::\n
\n
    $ aws login configure
    Entity ID [urn:mace:incommon:idp.edu]: urn:mace:uncommon:foo.com
    ECP Endpoint URL [https://idp.edu/idp/profile/SAML2/SOAP/ECP]:
''')

    def _run_main(self, args: Namespace, parsed_globals):
        return configure(args, self._session)
