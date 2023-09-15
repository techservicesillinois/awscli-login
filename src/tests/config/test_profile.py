from copy import copy
from os import path
from typing import Any, Dict

from awscli_login.config import JAR_DIR
from awscli_login.exceptions import (
    ProfileNotFound,
    ProfileMissingArgs,
)

from ..base import (
    TempDir,
)

from .base import ProfileBase


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
        self.Profile()

    def test_simple_config(self) -> None:
        """ Simple config with just a SAML section. """
        self.assertProfileHasAttrs(ecp_endpoint_url='foo')

    def test_bad_attr(self):
        """ Ensure AttributeError is thrown if a bad attr is referenced. """
        profile = self.Profile()
        with self.assertRaises(AttributeError):
            getattr(profile, 'manbearbig_does_not_exit')

    def test_bad_magic_cookies(self):
        """ Ensure cookies returns None if username is not set! """
        profile = self.Profile()

        self.assertEqual(
            profile.cookies,
            None,
            'The username has not been set so cookies must be None!'
        )


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
        self.login_config = """
[default]
ecp_endpoint_url = url
username = netid1
password = secret1
factor = push
role_arn = arn:aws:iam::account-id:role/role-name
enable_keyring = True
passcode = secret_code
duration = 900
http_header_factor = X_Foo
http_header_passcode = X_Bar
    """

    def test_full_config(self) -> None:
        """ Full config with User and SAML section """
        self.Profile()

        expected_attr_vals = {
            "ecp_endpoint_url": 'url',
            "username": 'netid1',
            "password": 'secret1',
            "factor": 'push',
            "role_arn": "arn:aws:iam::account-id:role/role-name",
            "enable_keyring": True,
            "passcode": "secret_code",
            "duration": 900,
            "http_header_factor": "X_Foo",
            "http_header_passcode": "X_Bar",
        }

        self.assertProfileHasAttrs(**expected_attr_vals)


class ReadFullProfileTestOverrides(ReadFullProfile):
    """ Override profile with cli args """

    def test_full_config(self) -> None:
        """ Testing command line args are processed. """
        args: Dict[str, Any] = {
            "ecp_endpoint_url": 'url2',
            "username": 'netid2',
            "password": 'secret2',
            "factor": 'sms',
            "role_arn": "arn:aws:iam::account-id:role/role-name2",
            "passcode": "secret",
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
            "passcode": "",
            "duration": 0,
            "http_header_factor": "",
            "http_header_passcode": "",
        }
        expected_attr_vals = copy(args)
        expected_attr_vals.update({'enable_keyring': False})
        args.update({'ask_password': True})

        self.Profile(profile='default', no_args=False, **args)
        self.assertProfileHasAttrs(**expected_attr_vals)


# This ensures that shared tests in mixins are not run with empty
# data sets!
del CookieMixin
del AttrTestMixin
