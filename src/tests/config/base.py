""" Base classes used for testing """
from argparse import Namespace
from typing import Any, Dict, List

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
    # Optional input cli arguments
    cli_args: Dict[str, Any] = {}

    profile_name: str = 'default'
    _session: MockSession
    _args: Namespace

    def setUp(self) -> None:
        super().setUp()

        self._args = login_cli_args(**self.cli_args)
        self._session = MockSession(self.profile_name)

    def Profile(self):
        self.profile = Profile(self._session, self._args)
        return self.profile

    def assertProfileHasAttr(self, attr: str, evalue) -> str:
        """ If called tests that profile has the given attribute
            and value. Returns None on success, and an error
            message on failure. """
        if not hasattr(self.profile, attr):
            return "Profile object does not have attr: %s" % attr

        rvalue = getattr(self.profile, attr)
        if type(rvalue) != type(evalue):
            return "Attribute %s has unexpected type %s! " \
                   "Expected %s!" % (attr, type(rvalue), type(evalue))

        if rvalue != evalue:
            return "Attribute %s has unexpected value %s! " \
                   "Expected %s!" % (attr, rvalue, evalue)

        return None

    def assertProfileHasAttrs(self, **kwargs) -> None:
        """ If called tests that profile has the expected
            attributes and values specifed in expected_attr_vals. """
        errors: List[str] = []

        for attr, value in kwargs.items():
            error = self.assertProfileHasAttr(attr, value)

            if error:
                errors.append(error)

        self.assertEqual(len(errors), 0, '\n'.join(errors))


class ProfileNoArgsBase(ProfileBase):
    """
    Like ProfileBase but without the ability to set Args.
    """
    profile: Profile

    def Profile(self):
        self.profile = Profile(self._session, None)
        return self.profile
