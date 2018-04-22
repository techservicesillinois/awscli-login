# from contextlib import redirect_stdout, redirect_stderr
# from io import StringIO
from unittest.mock import patch, call

from ..base import IntegrationTests
from ..util import fork


class TestNoProfile(IntegrationTests):
    """ Integration tests for no profile. """
    @fork()
    def test_logout_via_awscli(self):
        """ Logging out should throw AlreadyLoggedOut when not logged in. """
        mesg = 'Already logged out!\n'
        self.assertAwsCliReturns('logout', stderr=mesg, code=3)
        # TODO FIXME NO HARDCODE

    @fork()
    @patch('builtins.input', return_value='')
    def test_save_credentials_default_profile(self, mock_input):
        """ Creates a default entry in ~/.aws/credentials """
        calls = [
            call('ECP Endpoint URL [None]: '),
            call('Username [None]: '),
            call('Enable Keyring [False]: '),
            call('Duo Factor [None]: '),
            call('Role ARN [None]: '),
        ]

        self.assertAwsCliReturns('login', 'configure', code=0)
        mock_input.assert_has_calls(calls)
        self.assertEqual(len(mock_input.call_args_list), len(calls))


class TestDefaultProfile(IntegrationTests):
    """ Integration tests for default profile. """

    @fork()
    def test_logout_via_awscli(self):
        """ Logging out should throw AlreadyLoggedOut when not logged in. """
        self.profile = 'default'
        self.aws_credentials = """
[default]
aws_access_key_id = abc
aws_secret_access_key = def
aws_session_token = ghi
"""

        mesg = 'Already logged out!\n'
        self.assertAwsCliReturns('logout', stderr=mesg, code=3)
        # TODO FIXME NO HARDCODE ERROR CODES!
