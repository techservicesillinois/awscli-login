from copy import copy
from os import path
from os.path import isfile
from typing import Any, Dict
from unittest import SkipTest

from awscli_login.config import JAR_DIR
from awscli_login.exceptions import (
    AlreadyLoggedIn,
    ProfileNotFound,
    ProfileMissingArgs,
)

from ..base import (
    TempDir,
)

from .base import (
    ProfileBase,
    ProfileNoArgsBase,
)
from .util import qremove


class NoProfile(ProfileBase):
    """ Given an empty configuration. """

    def test_empty_config(self) -> None:
        """ Loading empty profile should throw Exception ProfileNotFound. """
        self.login_config = ''

        with self.assertRaises(ProfileNotFound):
            self.Profile()


class MissingProfile(ProfileBase):
    """ Given the desired profile is missing """
    profile_name = 'test'

    def test_missing_profile(self) -> None:
        """ Loading missing profile should throw Exception ProfileNotFound. """
        self.login_config = """
[default]
ecp_endpoint_url = foo
    """
        with self.assertRaises(ProfileNotFound):
            self.Profile()


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

    def test_has_pidfile_attr(self) -> None:
        """ Profile object should have a pidfile attr. """
        self.assertTrue(hasattr(self.profile, 'pidfile'))
        self.assertEqual(
            path.split(self.profile.pidfile)[1],
            self.profile_name + '.pid'
        )

    def test_raise_if_logged_in_no_pidfile(self) -> None:
        """ Should not throw exception if the pidfile does not exist. """
        if not hasattr(self.profile, 'pidfile'):
            raise SkipTest('Profile does not have attr pidfile!')
        if isfile(self.profile.pidfile):
            raise SkipTest('Test assumes pidfile is nonexistent!')

        self.profile.raise_if_logged_in()

    def test_raise_if_logged_in_with_pidfile(self) -> None:
        """ Should throw an exception if the pidfile exists. """
        if not hasattr(self.profile, 'pidfile'):
            raise SkipTest('Profile does not have attr pidfile!')
        with open(self.profile.pidfile, 'x') as f:
            f.write('1234')
        self.addCleanup(qremove, self.profile.pidfile)

        with self.assertRaises(AlreadyLoggedIn):
            self.profile.raise_if_logged_in()


class ReadMinProfile(ProfileNoArgsBase, AttrTestMixin):
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
        directory, _ = self._split_cookie_path()
        jar_dir = path.join(self.tmpd.name, JAR_DIR)

        self.assertEqual(
            directory,
            jar_dir,
            "Expected cookies to be in directory %s" % JAR_DIR
        )

    def test_cookies_filename(self):
        """ Cookie jar format should be user.txt. """
        _, filename = self._split_cookie_path()

        self.assertEqual(
            filename,
            self.profile.username + '.txt',
            "Expected cookies filename to have format user.txt"
        )


class ReadFullProfile(ProfileBase, CookieMixin):
    """ Test default profile using all options """
    expected_attr_vals = {
        "ecp_endpoint_url": 'url',
        "username": 'netid1',
        "password": 'secret1',
        "factor": 'push',
        "role_arn": "arn:aws:iam::account-id:role/role-name",
        "enable_keyring": True,
        "passcode": "secret_code",
        "verbose": 1,
        "refresh": 1500,
    }

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
verbose = 1
refresh = 1500
    """
        self.Profile()

    def test_full_config(self) -> None:
        """ Full config with User and SAML section """
        self.assertProfileHasAttrs(**self.expected_attr_vals)


class ReadFullProfileTestOverrides(ReadFullProfile):
    """ Override profile with cli args """

    cli_args: Dict[str, Any] = {
        "ecp_endpoint_url": 'url2',
        "username": 'netid2',
        "password": 'secret2',
        "factor": 'sms',
        "role_arn": "arn:aws:iam::account-id:role/role-name2",
        "passcode": "secret",
        "verbose": 2,
        "refresh": 1000,
    }
    expected_attr_vals = copy(cli_args)
    expected_attr_vals.update({'enable_keyring': False})
    cli_args.update({'ask_password': True})

    def test_full_config(self) -> None:
        """ Testing command line args are processed. """
        self.assertProfileHasAttrs(**self.expected_attr_vals)


# This ensures that shared tests in mixins are not run with empty
# data sets!
del(CookieMixin)
del(AttrTestMixin)
