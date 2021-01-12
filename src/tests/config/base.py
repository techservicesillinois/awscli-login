""" Base classes used for testing """
from typing import Any
from unittest.mock import patch

from awscli_login.config import Profile

from .util import MockSession
from ..util import login_cli_args
from ..base import CleanAWSLoginEnvironment


class ProfileBase(CleanAWSLoginEnvironment):
    """
    Base class for testing awscli_login.config.Profile.

    NOTA BENE: This class does NOT load self.profile and therefore is useful
    for testing failure conditions for Profile().
    """

    def Profile(self, profile: str = 'default', no_args: bool = False,
                **kwargs):
        args = None if no_args else login_cli_args(**kwargs)
        session = MockSession(profile)

        self.profile = Profile(session, args)
        return self.profile

    def assertProfileHasAttr(self, attr: str, evalue: Any) -> None:
        """ If called tests that profile has the given attribute
            and value. Returns None on success, and an error
            message on failure. """
        self.assertHasAttr(self.profile, attr, evalue)

    def assertProfileHasAttrs(self, **kwargs: Any) -> None:
        """ If called tests that profile has the expected
            attributes and values specifed in expected_attr_vals. """
        self.assertHasAttrs(self.profile, **kwargs)

    def patcher(self, target: Any, **kwargs):  # TODO FIXME
        patcher = patch(target, **kwargs)
        self.addCleanup(patcher.stop)

        return patcher.start()
