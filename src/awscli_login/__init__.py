# Rudimentary documentation for the aws-cli plugin API can be found
# here: https://github.com/aws/aws-cli/issues/1261
import logging

from argparse import Namespace

from awscli.customizations.commands import BasicCommand
from botocore.session import Session

from .__main__ import main, logout
from .configure import configure

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


class Login(BasicCommand):
    NAME = 'login'
    DESCRIPTION = ('is a plugin that manages retrieving and rotating'
                   ' Amazon STS keys using the Shibboleth IdP and Duo'
                   ' for authentication.')
    SYNOPSIS = ('aws login [<Arg> ...]')

    # tests/util.py:login_cli_args defaults must match this table
    ARG_TABLE = [
        # Ordering matches order in README.rst
        # Basic Properites (can be set interactively)
        {
            'name': 'ecp-endpoint-url',
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
        # Advancded Properites (can NOT be set interactively)
        {
            'name': 'disable-refresh',
            'default': None,
            'cli_type_name': 'boolean',
            'help_text': 'Disables automatic refresh of tokens'
        },
        {
            'name': 'refresh',
            'default': None,
            'cli_type_name': 'integer',
            'help_text': 'How often in seconds to refresh the STS credentials'
        },
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
    ]

    UPDATE = False

    def _run_main(self, args: Namespace, parsed_globals):
        main(args, self._session)
        return 0


class Logout(BasicCommand):
    NAME = 'logout'
    DESCRIPTION = ("Kills the process that renews the user's"
                   " credentials.")
    SYNOPSIS = ('aws logut')

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

    def _run_main(self, args: Namespace, parsed_globals):
        logout(args, self._session)
        return 0


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

* **ecp_endpoint_url** - The ECP endpoint URL of the IDP to use for authn
* **username** - The username to use on login to the IdP.
* **password** - The password to use on login to the IdP.
* **factor** - The Duo factor to use for 2FA
* **passcode** - A Duo passcode
* **role_arn** - The role ARN to select
* **enable_keyring** - If enabled retrieve password from keyring
* **disable_refresh** - Set to True to disable credential refresh
* **refresh** - How often in seconds to refresh credentials
* **duration** - Time in seconds credentials are valid
* **http_header_factor** - HTTP Header to store Duo factor
* **http_header_passcode** - HTTP Header to store passcode
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
        configure(args, self._session)
        return 0
