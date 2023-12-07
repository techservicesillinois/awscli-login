# from contextlib import redirect_stdout, redirect_stderr
# from io import StringIO
import unittest
import os

from multiprocessing import get_start_method
from unittest.mock import call

from ..base import IntegrationTests


@unittest.skipIf(
    os.environ.get('AWSCLI_LOGIN_FAST_TEST_ONLY'), 'Skipping slow test')
class TestNoProfile(IntegrationTests):
    """ Integration tests for no profile.

    This test takes about 2.16 seconds to run.
    """

    @unittest.skipIf(
        get_start_method() != 'fork',
        "This platform does not suppport fork!"
    )
    def test_logout_via_awscli(self):
        """ Logging out should throw AlreadyLoggedOut when not logged in. """
        mesg = 'Already logged out!\n'
        self.assertAwsCliReturns('logout', stderr=mesg, code=3)
        # TODO FIXME NO HARDCODE

    @unittest.skipIf(
        get_start_method() != 'fork',
        "This platform does not suppport fork!"
    )
    def test_login_configure_default_profile(self):
        """ Creates a default entry in ~/.aws-login/config """
        calls = [
            call('ECP Endpoint URL [None]: '),
            call('Username [None]: '),
            call('Enable Keyring [False]: '),
            call('Duo Factor [None]: '),
            call('Role ARN [None]: '),
        ]

        self.assertAwsCliReturns('login', 'configure', code=0, stderr=None,
                                 calls=calls)
