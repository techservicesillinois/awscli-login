# Rudimentary documentation for the aws-cli plugin API can be found
# here: https://github.com/aws/aws-cli/issues/1261
import logging

from argparse import Namespace

from awscli.customizations.commands import BasicCommand
from botocore.session import Session

from .__main__ import main, logout
from .configure import configure
from .account_names import print_account_names, save_account_names

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
    command_table['account_names'] = AccountNames(session)


class Login(BasicCommand):
    NAME = 'login'
    DESCRIPTION = ('is a plugin that manages retrieving and rotating'
                   ' Amazon STS keys using the Shibboleth IdP and Duo'
                   ' for authentication.')
    SYNOPSIS = ('aws login [<Arg> ...]')

    ARG_TABLE = [
        {'name': 'entity-id', 'help_text': 'Entity ID of the IdP'},
        {
            'name': 'ecp-endpoint-url',
            'help_text': 'ECP endpoint URL of the IdP'
        },
        {'name': 'username', 'help_text': 'Username to use on login to IdP'},
        {'name': 'password', 'help_text': 'Password to use on login to IdP'},
        {
            'name': 'role-arn',
            'help_text': 'The Role ARN to select. '
                         'If the IdP returns a single Role it is autoselected.'
        },
        {'name': 'factor', 'help_text': 'The Duo factor to use on login'},
        {'name': 'passcode', 'help_text': 'A Duo passcode'},
        {
            'name': 'refresh',
            'default': 0,
            'cli_type_name': 'integer',
            'help_text': 'How often in seconds to refresh the STS credentials'
        },
        {
            'name': 'verbose',
            'action': 'count',
            'default': 0,
            'cli_type_name': 'integer',
            'help_text': 'Display verbose output'
        },
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
            'name': 'duration',
            'default': None,
            'help_text': 'time in seconds that the token will last'
        },
        {
            'name': 'disable-refresh',
            'default': False,
            'cli_type_name': 'boolean',
            'help_text': 'Disables automatic refresh of tokens'
        },
    ]

    UPDATE = False

    def _run_main(self, args: Namespace, parsed_globals):
        main(args, self._session)
        return 0


class Logout(BasicCommand):
    NAME = 'logout'
    DESCRIPTION = ("Kills the process that is renewing the user's"
                   "credentials.")
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
entity ID and its ECP endpoint URL.  You can configure a named
profile using the --profile argument. If your config file does not
exist (the default location is ~/.aws-login/config), it will be
created for you. To keep an existing value, hit enter when prompted
for the value.  When you are prompted for information, the current
value will be dis- played in [brackets]. If the config item has
no value, it be displayed as [None].

=======================
Configuration Variables
=======================

The following configuration variables are supported in the config
file:

* **entity_id** - The entity ID of the IDP to use for authenitication
* **ecp_endpoint_url** - The ECP endpoint URL of the IDP to use for authn
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

class AccountNames(BasicCommand):
    NAME = 'account_names'
    DESCRIPTION = ('''
Print account names and account IDs
=======================
Configuration Variables
=======================

''')
    SYNOPSIS = ('aws login account_names')

    ARG_TABLE = [
        {
            'name': 'verbose',
            'action': 'count',
            'default': 0,
            'cli_type_name': 'integer',
            'help_text': 'Display verbose output'
        },
        {
            'name': 'save',
            'action': 'store_true',
            'default': False,
            'cli_type_name': 'boolean',
            'help_text': 'Update accounts.ini file with names'
        },
    ]

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

        if args.save:
            save_account_names(args, self._session)
        else:
            print_account_names(args, self._session)

        return 0
