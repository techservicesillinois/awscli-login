from unittest.mock import call, patch

from botocore.session import Session

from awscli_login.configure import configure
from .base import CleanTestEnvironment
from .util import login_cli_args


# TODO Not very dry...
class TestNoProfile(CleanTestEnvironment):
    """ Integration tests for no profile. """
    profile = None  # default

    @patch('builtins.input', return_value='')
    def test_save_credentials_default_profile(self, mock_input):
        """ Creates a default entry in ~/.aws/credentials """
        args = login_cli_args()
        session = Session()
        with self.assertRaises(SystemExit) as e:
            configure(args, session)

        self.assertEqual(e.exception.code, 0)
        mock_input.assert_has_calls(
            [
                call('ECP Endpoint URL [None]: '),
                call('Username [None]: '),
                call('Enable Keyring [False]: '),
                call('Duo Factor [None]: '),
                call('Role ARN [None]: '),
            ],
        )
        self.assertEqual(len(mock_input.call_args_list), 5)
