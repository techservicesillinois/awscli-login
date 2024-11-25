from copy import copy
from datetime import datetime
from os import path
from os.path import isfile
from typing import Any, Dict

from awscli_login.config import JAR_DIR
from awscli_login.exceptions import (
    AlreadyLoggedIn,
    AlreadyLoggedOut,
    ProfileMissingArgs,
    ProfileNotFound,
)

from ..base import (
    TempDir,
)

from .base import ProfileBase
from .util import test_token


class NoProfile(ProfileBase):
    """ Given an empty configuration. """

    def test_empty_config(self) -> None:
        """ Loading empty profile should throw Exception ProfileNotFound. """
        self.login_config = ''

        with self.assertRaises(ProfileNotFound):
            self.Profile()


class MissingProfile(ProfileBase):
    """ Given the desired profile is missing """

    def test_missing_profile(self) -> None:
        """ Loading missing profile should throw Exception ProfileNotFound. """
        self.login_config = """
[default]
ecp_endpoint_url = foo
    """
        with self.assertRaises(ProfileNotFound):
            self.Profile('test')


class EmptyProfile(ProfileBase):
    """ Given an empty default profile. """

    def test_profile_with_no_args(self) -> None:
        """ Profile having no attrs should throw ProfileMissingArgs. """
        self.login_config = """
[default]
    """

        with self.assertRaises(ProfileMissingArgs):
            self.Profile()


class AttrTestMixin(ProfileBase):
    """ Mixin class of attribute tests valid for any profile. """

    def test_magic_attrs(self):
        """ Ensure AttributeError is thrown if a bad attr is referenced. """
        with self.assertRaises(AttributeError):
            getattr(self.profile, 'manbearbig_does_not_exit')

    def test_has_cookies_attr(self):
        """ Profile object should have a cookies attr. """
        self.assertTrue(
            hasattr(self.profile, 'cookies'),
            "Profile does not have the cookies attribute!"
        )

    def test_cookies_attr_in_dir(self):
        """ The cookies attribute should be visible in dir(profile). """
        self.assertIn(
            'cookies',
            dir(self.profile),
            "Cookies attribute not listed in dir(profile)!"
        )


class ReadMinProfile(AttrTestMixin):
    """ Test profile with minimum valid default profile """

    def setUp(self) -> None:
        super().setUp()
        self.login_config = """
[default]
ecp_endpoint_url = foo
    """
        # No credential file exists
        self.Profile()

    # Do not overload the property login_credentials directly,
    # because super() does not support setters. For some reason,
    # Python discourages the use of properties in inheritance:
    # https://realpython.com/python-getter-setter
    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name == "login_credentials":
            self.profile.reload()  # Reload modified file from disk

    def test_simple_config(self) -> None:
        """ Simple config with just a SAML section. """
        self.assertProfileHasAttrs(ecp_endpoint_url='foo')

    def test_bad_attr(self):
        """ Ensure AttributeError is thrown if a bad attr is referenced. """
        with self.assertRaises(AttributeError):
            getattr(self.profile, 'manbearbig_does_not_exit')

    def test_bad_magic_cookies(self):
        """ Ensure cookies returns None if username is not set! """
        self.assertEqual(
            self.profile.cookies,
            None,
            'The username has not been set so cookies must be None!'
        )

    def test_raise_if_logged_in_no_credential_file(self):
        """Ensure no exception is raised if no credential file exists."""
        self.assertFalse(isfile(self.login_credentials_path))

        self.profile.raise_if_logged_in()
        self.assertRaises(AlreadyLoggedOut, self.profile.raise_if_logged_out)

    def test_raise_if_logged_in_empty_credential_file(self):
        """Ensure no exception is raised if empty credential file exists."""
        self.login_credentials = ""
        self.profile.raise_if_logged_in()
        self.assertRaises(AlreadyLoggedOut, self.profile.raise_if_logged_out)

    def test_raise_if_logged_in_empty_credential(self):
        """Ensure exception is not raised with empty credential."""
        self.login_credentials = """[default]
            aws_access_key_id =
            aws_secret_access_key =
            aws_session_token =
            aws_security_token =
            aws_principal_arn =
            aws_role_arn =
            expiration = """
        self.profile.raise_if_logged_in()
        self.assertRaises(AlreadyLoggedOut, self.profile.raise_if_logged_out)

    def test_raise_if_logged_in_valid_credential_file(self):
        """Ensure exception is raised with valid credentials."""
        self.login_credentials = """[default]
            aws_access_key_id = ABCDEFGHIJKLMNOPQRSTUVWXYZ
            aws_secret_access_key = 1234567890
            aws_session_token = reallycooltoken
            aws_security_token = securitytoken
            aws_principal_arn = somearn
            aws_role_arn = someotherarn
            expiration = 2100-07-13T17:54:39"""
        self.assertRaises(AlreadyLoggedIn, self.profile.raise_if_logged_in)
        self.profile.raise_if_logged_out()

    def test_raise_if_logged_in_empty_arn_credential_file(self):
        """Ensure exception is not raised when aws_role_arn is not set."""
        self.login_credentials = """[default]
            aws_access_key_id = ABCDEFGHIJKLMNOPQRSTUVWXYZ
            aws_secret_access_key = 1234567890
            aws_session_token = reallycooltoken
            aws_security_token = securitytoken
            aws_principal_arn = somearn
            aws_role_arn =
            expiration = 1970-01-01T17:54:39Z"""
        self.profile.raise_if_logged_in()
        self.assertRaises(AlreadyLoggedOut, self.profile.raise_if_logged_out)

    def test_raise_if_logged_in_missing_arn_credential_file(self):
        """Ensure exception is not raised when aws_role_arn is missing."""
        self.login_credentials = """[default]
            aws_access_key_id = ABCDEFGHIJKLMNOPQRSTUVWXYZ
            aws_secret_access_key = 1234567890
            aws_session_token = reallycooltoken
            aws_security_token = securitytoken
            aws_principal_arn = somearn
            expiration = 1970-01-01T17:54:39Z"""
        self.profile.raise_if_logged_in()
        self.assertRaises(AlreadyLoggedOut, self.profile.raise_if_logged_out)

    def test_are_credentials_expired(self):
        """Ensure return True when expiration is expired."""
        self.login_credentials = """[default]
            expiration = 1970-01-01T17:54:39Z"""
        self.assertTrue(self.profile.are_credentials_expired())

    def test_are_credentials_expired_invalid(self):
        """Ensure return True when expiration is invalid."""
        self.login_credentials = """[default]
            expiration = abc"""
        self.assertTrue(self.profile.are_credentials_expired())

    def test_are_credentials_expired_missing_expiration(self):
        """Ensure return True when expiration is missing."""
        self.login_credentials = "[default]\n"
        self.assertTrue(self.profile.are_credentials_expired())

    def test_are_credentials_expired_not_expired(self):
        """Ensure return False when credentials are not expired."""
        self.login_credentials = """[default]
            expiration = 2100-07-13T17:54:39"""
        self.assertFalse(self.profile.are_credentials_expired())

    def test_load_credentials(self):
        """Ensure can load credentials."""
        token = {
            'Credentials': {
                'AccessKeyId': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                'SecretAccessKey': '1234567890',
                'SessionToken': 'reallycooltoken',
                'Expiration': datetime(2100, 7, 13, 17, 54, 39),
            }
        }
        self.login_credentials = """[default]
            aws_access_key_id = ABCDEFGHIJKLMNOPQRSTUVWXYZ
            aws_secret_access_key = 1234567890
            aws_session_token = reallycooltoken
            aws_security_token = securitytoken
            aws_principal_arn = somearn
            aws_role_arn = someotherarn
            expiration = 2100-07-13T17:54:39"""
        self.assertEqual(token, self.profile.load_credentials())

    def test_load_credentials_invalid_expiration(self):
        """Ensure can load credentials."""
        token = {
            'Credentials': {
                'AccessKeyId': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                'SecretAccessKey': '1234567890',
                'SessionToken': 'reallycooltoken',
                'Expiration': datetime(2100, 7, 13, 17, 54, 39),
            }
        }
        self.login_credentials = """[default]
            aws_access_key_id = ABCDEFGHIJKLMNOPQRSTUVWXYZ
            aws_secret_access_key = 1234567890
            aws_session_token = reallycooltoken
            aws_security_token = reallycooltoken
            aws_principal_arn = somearn
            aws_role_arn = someotherarn
            expiration = 2100-07-13T17:54:39"""
        self.assertEqual(token, self.profile.load_credentials())

    def test_load_credentials_empty_file(self):
        """Ensure None is returned if credentials file is empty."""
        self.assertEqual(None, self.profile.load_credentials())

    def test_load_credentials_incomplete_credentials(self):
        """Ensure None is returned if credentials are incomplete."""
        self.login_credentials = """[default]
            aws_secret_access_key = 1234567890
            aws_session_token = reallycooltoken
            aws_security_token = reallycooltoken
            aws_principal_arn = somearn
            aws_role_arn = someotherarn
            expiration = 2100-07-13T17:54:39"""
        self.assertEqual(None, self.profile.load_credentials())


class CookieMixin(TempDir):
    """
    Mixin class for testing awscli_login.config.Profile cookies.

    NOTA BENE: These tests assume that the username attribute has
    been set, and that self.profile has been set by setUp.
    """

    def _split_cookie_path(self):
        """ Returns a tuple (path, filename) for the cookie jar. """
        cookies = self.profile.cookies

        self.assertNotEqual(
            self.profile.username,
            None,
            'This test will fail if the username is not set!'
        )

        self.assertNotEqual(
            cookies,
            None,
            'The username is set so why no cookie?'
        )
        return path.split(cookies)

    def test_cookies_path(self):
        """ Cookie jar should live in ~/.aws-config/cookies. """
        self.Profile()

        directory, _ = self._split_cookie_path()
        jar_dir = path.join(self.tmpd.name, JAR_DIR)

        self.assertEqual(
            directory,
            jar_dir,
            "Expected cookies to be in directory %s" % JAR_DIR
        )

    def test_cookies_filename(self):
        """ Cookie jar format should be user.txt. """
        self.Profile()
        _, filename = self._split_cookie_path()

        self.assertEqual(
            filename,
            self.profile.username + '.txt',
            "Expected cookies filename to have format user.txt"
        )


class ReadFullProfile(ProfileBase, CookieMixin):
    """ Test default profile using all options """

    def setUp(self) -> None:
        super().setUp()
        self.args = {
            "ecp_endpoint_url": 'url',
            "username": 'netid1',
            "password": 'secret1',
            "factor": 'push',
            "role_arn": "arn:aws:iam::account-id:role/role-name",
            "enable_keyring": True,
            "duration": 900,
            "http_header_factor": "X_Foo",
            "http_header_passcode": "X_Bar",
        }

        self.login_config = "[default]\n" + "\n".join(
            [f"{k} = {v}" for k, v in self.args.items()]
        ) + "\n"

        self.args['passcode'] = None

    def test_full_config(self) -> None:
        """ Full config with User and SAML section """
        self.Profile()

        expected_attr_vals = self.args
        self.assertProfileHasAttrs(**expected_attr_vals)


class ReadFullProfileTestOverrides(ReadFullProfile):
    """ Override profile with cli args """

    # Regression test for issue #117
    def test_passcode_factor_override(self) -> None:
        """ Passcode set at the command line overrides factor. """
        args: Dict[str, Any] = {
            "passcode": "secret",
        }
        expected_attr_vals = copy(self.args)
        expected_attr_vals.update(args)
        expected_attr_vals["factor"] = "passcode"

        self.assertNotEqual(self.args["factor"], "passcode")
        self.Profile(profile='default', no_args=False, **args)
        self.assertProfileHasAttrs(**expected_attr_vals)

    def test_full_config(self) -> None:
        """ Testing command line args are processed. """
        args: Dict[str, Any] = {
            "ecp_endpoint_url": 'url2',
            "username": 'netid2',
            "password": 'secret2',
            "factor": 'sms',
            "role_arn": "arn:aws:iam::account-id:role/role-name2",
            "duration": 1500,
            "http_header_factor": "X_Bar",
            "http_header_passcode": "X_Foo",
        }
        expected_attr_vals = copy(args)
        expected_attr_vals.update({'enable_keyring': False})
        args.update({'ask_password': True})

        self.Profile(profile='default', no_args=False, **args)
        self.assertProfileHasAttrs(**expected_attr_vals)

    def test_logically_false_args_full_config(self) -> None:
        """ Testing logically False command line args override config. """
        args: Dict[str, Any] = {
            "ecp_endpoint_url": '',
            "username": '',
            "password": '',
            "factor": '',
            "role_arn": "",
            "duration": 0,
            "http_header_factor": "",
            "http_header_passcode": "",
        }
        expected_attr_vals = copy(args)
        expected_attr_vals.update({'enable_keyring': False})
        args.update({'ask_password': True})

        self.Profile(profile='default', no_args=False, **args)
        self.assertProfileHasAttrs(**expected_attr_vals)


class TestCredentials(ReadFullProfile):

    def setUp(self):
        super().setUp()
        self.login_credentials = """[wtf]
aws_access_key_id = 123
aws_secret_access_key = 456
aws_session_token = 789
aws_security_token = 789

"""
        self.Profile(profile='default', no_args=True)

    def test_save_credentials(self):
        """ Test save to ~/.aws-login/credentials """

        credentials = self.login_credentials
        credentials += """[default]
aws_access_key_id = a
aws_secret_access_key = b
aws_session_token = c
aws_security_token = c
expiration = 2021-02-11T00:42:09Z
aws_principal_arn = love
aws_role_arn = thunder
username = NetID

"""
        role = ('love', 'thunder')
        self.profile.username = "NetID"
        self.profile.save_credentials(test_token('a', 'b', 'c'), role)
        self.assertCredentialsFileEquals(credentials)


class TestLoadFromCredentialsFile(ProfileBase):

    def test_login_credentials_loaded(self):
        """ Ensure username and role are loaded from login_credentials. """
        self.login_config = """
[default]
ecp_endpoint_url = url
"""
        self.login_credentials = """[default]
aws_principal_arn = love
aws_role_arn = thunder
username = thor
"""
        self.Profile(profile='default', no_args=True)
        self.assertEqual(self.profile.username, "thor")
        self.assertEqual(self.profile.role_arn, "thunder")

    def test_login_credentials_not_loaded(self):
        """ Ensure username and role are not loaded from login_credentials. """
        self.login_config = """
[default]
ecp_endpoint_url = url
username = thor
role_arn = jane
"""
        self.login_credentials = """[default]
aws_principal_arn = love
aws_role_arn = thunder
username = NetID
"""
        self.Profile(profile='default', no_args=True)

        self.assertEqual(self.profile.username, "thor")
        self.assertEqual(self.profile.role_arn, "jane")


# This ensures that shared tests in mixins are not run with empty
# data sets!
del CookieMixin
del AttrTestMixin
