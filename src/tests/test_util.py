import os
import unittest

from datetime import datetime, timezone
from io import StringIO
from multiprocessing import get_start_method
from os.path import isfile
from typing import Any, Dict
from unittest.mock import patch

from botocore.session import Session

from awscli_login.const import ERROR_INVALID_PROFILE_ROLE
from awscli_login.exceptions import SAML
from awscli_login.util import (
    get_selection,
    remove_credentials,
    save_credentials,
    secure_touch,
    sort_roles,
)

from .util import fork, ForkException
from .base import CleanAWSEnvironment, TempDir


def token(akey: str, skey: str, stoken: str) -> Dict[str, Dict[str, Any]]:
    return {
               'Credentials': {
                                  'AccessKeyId': akey,
                                  'SecretAccessKey': skey,
                                  'SessionToken': stoken,
                                  'Expiration': datetime.now(timezone.utc)
                              }
           }


# This must be here due to pickle errors.
class WTF(Exception):
    pass


class util(unittest.TestCase):

    @unittest.skipIf(
        get_start_method() != 'fork',
        "This platform does not suppport fork!"
    )
    def test_fork_return_value(self):
        """ forked function can return a value """
        @fork()
        def add(x, y):
            return x + y

        self.assertEqual(add(1, 2), 3)

    @unittest.skipIf(
        get_start_method() != 'fork',
        "This platform does not suppport fork!"
    )
    def test_fork_raises_exception(self):
        """ forked function can raise an exception """
        mesg = "What the fork!?"

        @fork()
        def wtf():
            raise Exception(mesg)

        with self.assertRaises(ForkException) as cm:
            wtf()

        self.assertEqual(str(cm.exception), "<class 'Exception'>: %s" % mesg)

    @unittest.skipIf(
        get_start_method() != 'fork',
        "This platform does not suppport fork!"
    )
    def test_fork_raises_custom_exception(self):
        """ forked function can raise a custom exception """
        mesg = "What the fsck!?"

        # # This class can NOT be defined here!
        # # If it is you get a pickle exception.
        #  class WTF(Exception):
        #     pass

        @fork()
        def wtf():
            raise WTF(mesg)

        with self.assertRaises(ForkException) as cm:
            wtf()

        self.assertEqual(cm.exception.etype, WTF)
        self.assertEqual(cm.exception.message, mesg)

    @patch('builtins.input', return_value=0)
    def test_get_single_selection(self, mock_input):
        """ When a single role is returned by the IdP do not ask for input """
        roles = [('idp', 'arn:aws:iam::224588347132:role/KalturaAdmin')]

        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            self.assertEqual(get_selection(roles), roles[0])

            mock_input.assert_not_called()

            output = mock_stdout.getvalue()
            self.assertEqual(output, "", "get_selection printed output:"
                             "\n%s\n----\n" % output)

    @patch('builtins.input', return_value=0)
    @patch('sys.stdout', new=StringIO())
    def test_get_1of2_selections(self, *args):
        """ Select the first of two roles """
        roles = [
            ('idp1', 'arn:aws:iam::224588347132:role/KalturaAdmin'),
            ('idp2', 'arn:aws:iam::617683844790:role/BoxAdmin'),
        ]

        self.assertEqual(get_selection(roles), roles[0])

    @patch('builtins.input', return_value=1)
    @patch('sys.stdout', new=StringIO())
    def test_get_2of2_selections(self, *args):
        """ Select the second of two roles """
        roles = [
            ('idp1', 'arn:aws:iam::224588347132:role/KalturaAdmin'),
            ('idp2', 'arn:aws:iam::617683844790:role/BoxAdmin'),
        ]

        self.assertEqual(get_selection(roles), roles[1])

    @patch('builtins.input', return_value=1)
    def test_selections_profile_role(self, *args):
        """ Profile role is selected when valid and present """
        roles = [
            ('idp1', 'arn:aws:iam::224588347132:role/KalturaAdmin'),
            ('idp2', 'arn:aws:iam::617683844790:role/BoxAdmin'),
        ]
        profile_role = roles[1][1]

        with patch('sys.stdout', new=StringIO()) as stdout:
            role = get_selection(roles, profile_role)

            self.assertEqual(
                 stdout.getvalue(),
                 '',
                 'User was prompted for a selection '
                 'even though the Profile role was set!'
            )

        self.assertEqual(
            role,
            roles[1],
            'Profile role was not selected!'
        )

    @patch('builtins.input', return_value=1)
    def test_selections_bad_profile_role(self, *args):
        """ If a bad Profile role is set, then get_selection prompts the user.
        """
        profile_role = 'arn:aws:iam::617683844790:role/BadRole'

        roles = [
            ('idp1', 'arn:aws:iam::224588347132:role/KalturaAdmin'),
            ('idp2', 'arn:aws:iam::617683844790:role/BoxAdmin'),
        ]

        with patch('sys.stdout', new=StringIO()):
            with self.assertLogs('awscli_login.util', 'ERROR') as cm:
                get_selection(roles, profile_role)

        error = ERROR_INVALID_PROFILE_ROLE % profile_role
        self.assertEqual(
            cm.output,
            ["ERROR:awscli_login.util:%s" % error],
        )

    def test_get_empty_selection(self, *args):
        """ Attempt to select from an empty role set """
        with self.assertRaises(SAML):
            get_selection([])

    def test_sort_roles(self, *args):
        """ Sort role arns by account and role. """
        roles = [
            ('idp1', 'arn:aws:iam::617683844790:role/KalturaAdmin'),
            ('idp1', 'arn:aws:iam::224588347132:role/KalturaAdmin'),
            ('idp1', 'arn:aws:iam::224588347132:role/ASFoobarTeam'),
        ]

        expected = [
            ('224588347132', [(2, 'ASFoobarTeam'), (1, 'KalturaAdmin')]),
            ('617683844790', [(0, 'KalturaAdmin')]),
        ]

        output = sort_roles(roles)
        self.assertEqual(
            expected,
            output,
            'Accounts & roles were not sorted as expected!'
            '\nReturned: %s'
            '\nExpected: %s' % (output, expected)
        )


class SaveDefaultCreds(CleanAWSEnvironment):

    def test_save_credentials_default_profile(self):
        """ Creates a default entry in non-existent ~/.aws/credentials """
        self.profile = None  # default
        credentials = """[default]
aws_access_key_id = foo
aws_secret_access_key = bar
aws_session_token = yep
aws_security_token = yep
"""

        session = Session()
        save_credentials(session, token('foo', 'bar', 'yep'))
        self.assertAwsCredentialsEquals(credentials)

    def test_save_credentials_not_default_profile(self):
        """ Creates a non-default entry in empty ~/.aws/credentials """
        self.profile = 'wtf'
        credentials = """[wtf]
aws_access_key_id = a
aws_secret_access_key = b
aws_session_token = c
aws_security_token = c
"""

        session = Session()
        save_credentials(session, token('a', 'b', 'c'))
        self.assertAwsCredentialsEquals(credentials)

    def test_remove_credentials_default_profile(self):
        """ Removes default entry in ~/.aws/credentials """
        self.profile = 'default'
        self.aws_credentials = """
[default]
aws_access_key_id = foo
aws_secret_access_key = bar
aws_session_token = yep
aws_security_token = yep
"""

        credentials = "\n[default]\n" \
                      "aws_access_key_id = \n" \
                      "aws_secret_access_key = \n" \
                      "aws_session_token = \n" \
                      "aws_security_token = \n"

        session = Session()
        remove_credentials(session)
        self.assertAwsCredentialsEquals(credentials)


class TestDontClobberCommentsBase(CleanAWSEnvironment):

    def setUp(self):
        super().setUp()
        self.aws_credentials = """
# This is an example credentials files with comments
# and old entries

[default]
aws_access_key_id = abc
aws_secret_access_key = def
aws_session_token = ghi
aws_security_token = ghi

# Test

[wtf]
aws_access_key_id = 123
aws_secret_access_key = 456
aws_session_token = 789
aws_security_token = 789

# Test
"""

    def test_save_credentials_comments_not_clobbered(self):
        """ Ensure comments are not clobbered in ~/.aws/credentials """
        self.profile = 'foo'

        credentials = self.aws_credentials
        credentials += """[foo]
aws_access_key_id = a
aws_secret_access_key = b
aws_session_token = c
aws_security_token = c
"""
        session = Session()
        save_credentials(session, token('a', 'b', 'c'))
        self.assertAwsCredentialsEquals(credentials)

    def test_remove_credentials_non_default_profile(self):
        """ Removes non-default entry in ~/.aws/credentials """
        self.profile = 'foo'

        credentials = self.aws_credentials
        credentials += "\n[foo]\n" \
                       "aws_access_key_id = \n" \
                       "aws_secret_access_key = \n" \
                       "aws_session_token = \n" \
                       "aws_security_token = \n"

        self.aws_credentials += """
[foo]
aws_access_key_id = a
aws_secret_access_key = b
aws_session_token = c
aws_security_token = c
"""

        session = Session()
        remove_credentials(session)
        self.assertAwsCredentialsEquals(credentials)


class SecureTouchTests(TempDir):
    """ Tests for the function secure_touch. """

    def test_secure_touch_function_creates_file(self):
        """Newly created file by secure_touch should have perms 0x600. """
        path = self._abspath('foo.txt')
        secure_touch(path)

        self.assertTrue(isfile(path), 'Failed to create file!')
        if os.name == 'posix':
            self.assertHasFilePerms(path, owner='rw')

    def test_secure_touch_function_changes_perms(self):
        """File with perms 0x644 should be 0x600 after secure_touch. """
        path = self._abspath('foo.txt')

        fd = os.open(path, os.O_CREAT | os.O_RDONLY, mode=0o644)
        os.close(fd)

        secure_touch(path)
        if os.name == 'posix':
            self.assertHasFilePerms(path, owner='rw')


if __name__ == '__main__':
    suite = unittest.TestSuite()
    unittest.main()
