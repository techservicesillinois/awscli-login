import os
import stat
import unittest

from argparse import Namespace
from io import StringIO
from multiprocessing import get_start_method
from os.path import isfile
from unittest.mock import patch

from botocore.session import Session

from awscli_login.const import ERROR_INVALID_PROFILE_ROLE
from awscli_login.exceptions import (
    CredentialProcessMisconfigured,
    CredentialProcessNotSet,
    InvalidSelection,
    SAML,
    TooManyHttpTrafficFlags,
)
from awscli_login.util import (
    config_vcr,
    get_selection,
    secure_touch,
    sort_roles,
)
from awscli_login.util import (
    raise_if_credential_process_not_set,
    update_credential_file,
)

from .util import fork, ForkException
from .base import CleanAWSEnvironment, TempDir


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

    @patch('builtins.input', return_value=3)
    @patch('sys.stdout', new=StringIO())
    def test_get_bad_numeric_selection(self, *args):
        """ Invalid numeric selection of two roles """
        roles = [
            ('idp1', 'arn:aws:iam::123577191723:role/KalturaAdmin'),
            ('idp2', 'arn:aws:iam::271867855970:role/BoxAdmin'),
        ]

        with self.assertRaises(InvalidSelection):
            get_selection(roles)

    @patch('builtins.input', return_value="foo")
    @patch('sys.stdout', new=StringIO())
    def test_get_bad_type_selection(self, *args):
        """ Invalid string selection of two roles """
        roles = [
            ('idp1', 'arn:aws:iam::123577191723:role/KalturaAdmin'),
            ('idp2', 'arn:aws:iam::271867855970:role/BoxAdmin'),
        ]

        with self.assertRaises(InvalidSelection):
            get_selection(roles)

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

    def test_config_vcr(self):
        self.assertEqual(config_vcr(Namespace()), (None, None))

        ns = Namespace(load_http_traffic="foo", save_http_traffic="bar")
        self.assertRaises(TooManyHttpTrafficFlags, config_vcr, ns)

        ns = Namespace(load_http_traffic="foo", save_http_traffic=None)
        self.assertEqual(config_vcr(ns), ("foo", True))
        self.assertNotIn("load_http_traffic", ns)
        self.assertNotIn("save_http_traffic", ns)

        ns = Namespace(load_http_traffic=None, save_http_traffic="bar")
        self.assertEqual(config_vcr(ns), ("bar", False))
        self.assertNotIn("load_http_traffic", ns)
        self.assertNotIn("save_http_traffic", ns)


class SaveDefaultCreds(CleanAWSEnvironment):

    def test_credential_process_not_set(self):
        """Ensure raises CredentialProcessNotSet"""
        self.profile = 'default'
        self.aws_credentials = ''
        session = Session()
        self.assertRaises(CredentialProcessNotSet,
                          raise_if_credential_process_not_set,
                          session, self.profile)

    def test_credential_process_invalid(self):
        """Ensure raises CredentialProcessInvalid"""
        self.profile = 'default'
        self.aws_credentials = """[default]
        credential_process = foo
        """
        session = Session()
        self.assertRaises(CredentialProcessMisconfigured,
                          raise_if_credential_process_not_set,
                          session, self.profile)

    def test_credential_process_valid(self):
        """Ensure does not raise exception"""
        self.profile = 'default'
        path = self.write("aws-login", "")
        # Windows Python versions 3.6, 3.7, and 3.8 require
        # that files created in a temporary directory are
        # writable otherwise cleanup will fail on deletion (#133)
        os.chmod(path, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
        self.aws_credentials = f"""[default]
        credential_process = {path} --profile default
        """
        session = Session()
        raise_if_credential_process_not_set(session, self.profile)


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

    def test_update_credential_file_comments_not_clobbered(self):
        """ Ensure comments are not clobbered in ~/.aws/credentials """
        self.profile = 'foo'

        credentials = self.aws_credentials
        credentials += """[foo]
credential_process = aws-login --profile foo
"""

        session = Session()
        self.assertTrue(update_credential_file(session, self.profile))
        self.assertAwsCredentialsEquals(credentials)

    @patch('builtins.input', return_value='n')
    def test_update_credential_no_change(self, mock_input):
        """ Ensure credentials are not updated if user answers no """
        self.profile = 'wtf'
        credentials = self.aws_credentials

        session = Session()
        self.assertFalse(update_credential_file(session, self.profile))
        self.assertAwsCredentialsEquals(credentials)
        mock_input.assert_called_once()

    @patch('builtins.input', return_value='y')
    def test_update_credential_file_keys_are_removed(self, *args):
        """ Ensure old keys are removed  ~/.aws/credentials """
        credentials = """
# This is an example credentials files with comments
# and old entries

[default]
aws_access_key_id = abc
aws_secret_access_key = def
aws_session_token = ghi
aws_security_token = ghi

# Test

[wtf]
credential_process = aws-login --profile wtf

# Test
"""

        self.profile = 'wtf'
        session = Session()
        self.assertTrue(update_credential_file(session, self.profile))
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
