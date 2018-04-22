from copy import copy
from typing import Any, List
from unittest.mock import Mock, patch  # call

from awscli_login.exceptions import InvalidFactor

from .base import ProfileBase


class Creds():

    def __init__(self, username: str=None, password: str=None,
                 factor: str=None, passcode: str=None,
                 keyring: str=None) -> None:
        self.username = username
        self.password = password
        self.factor = factor
        self.passcode = passcode
        self.keyring = keyring

    def get(self) -> List[str]:
        r = []

        if self.username is not None:
            r.append(self.username)

        if self.factor is not None:
            r.append(self.factor)

        if self.passcode is not None:
            r.append(self.passcode)

        return r


class GetCredsProfileBase(ProfileBase):
    inputs: Creds  # User inputs
    outputs: Creds  # Expected output

    def patcher(self, target: Any, side_effect=None) -> Mock:
        patcher = patch(
            target,
            autospec=True,
            side_effect=side_effect,

        )
        r = patcher.start()
        self.addCleanup(patcher.stop)

        return r

    def setUp(self) -> None:
        self.mock_input = self.patcher('builtins.input', self.inputs.get())

        self.mock_password = self.patcher('awscli_login.config.getpass',
                                          [self.inputs.password])

        self.mock_get_password = self.patcher(
            'awscli_login.config.get_password',
            [self.inputs.keyring],
        )
        self.mock_set_password = self.patcher(
            'awscli_login.config.set_password'
        )
        super().setUp()

    def _test_get_credentials(self):
        # Ensure actual outputs equal expected outputs
        errors = []
        mesg = 'get_credentials returned %s: %s. Expected: %s.'

        # Ensure no error messages logged
        try:
            with self.assertLogs() as logs:
                usr, pwd, hdr = self.profile.get_credentials()
        except AssertionError:
            # If nothing is logged then an AssertionError is raised
            pass
        else:
            raise AssertionError("Unexpected error: %s" % logs.output)

        pairs = [
            ('username', usr),
            ('password', pwd),
            ('factor', hdr.get('X-Shiboleth-Duo-Factor')),
            ('passcode', hdr.get('X-Shiboleth-Duo-Passcode')),
        ]

        for name, ret in pairs:
            expected = getattr(self.outputs, name)

            if (ret != expected):
                errors.append(mesg % (name, ret, expected))

        if errors:
            raise AssertionError('\n'.join(errors))

        # Make sure the user was prompted for exactly the inputs given
        self.assertEqual(self.mock_input.call_count, len(self.inputs.get()))

        if self.inputs.password:
            self.mock_password.assert_called_once()
        else:
            self.mock_password.assert_not_called()

        if self.profile.enable_keyring:
            self.mock_get_password.assert_called_once()
            self.mock_set_password.assert_called_once()
        else:
            self.mock_get_password.assert_not_called()
            self.mock_set_password.assert_not_called()


class GetCredsMinProfileBase(GetCredsProfileBase):
    """ Minimal default profile with no tests. """

    def setUp(self) -> None:
        super().setUp()
        self.login_config = """
[default]
ecp_endpoint_url = foo
    """
        self.Profile()


class GetCredsMinProfileBadFactorTest(GetCredsMinProfileBase):
    """ Test minimal default profile with factor passcode. """
    inputs = Creds(username="user", password="secret", factor="bozo")
    outputs = copy(inputs)

    def test_get_credentials(self):
        """ Should prompt for all user credentials. """
        with self.assertRaises(InvalidFactor):
            usr, pwd, hdr = self.profile.get_credentials()


class GetCredsMinProfilePushTest(GetCredsMinProfileBase):
    """ Test minimal default profile with factor passcode. """
    inputs = Creds(username="user", password="secret", factor="passcode",
                   passcode="1234")
    outputs = copy(inputs)

    def test_get_credentials(self):
        """ Should prompt for all user credentials. """
        self._test_get_credentials()


class GetCredsMinProfilePhoneTest(GetCredsMinProfileBase):
    """ Test minimal default profile with factor phone. """
    inputs = Creds(username="user", password="secret", factor="phone")
    outputs = copy(inputs)

    def test_get_credentials(self):
        """ Should accept phone factor. """
        self._test_get_credentials()


class GetCredsMinProfileNoFactorTest(GetCredsMinProfileBase):
    """ Test minimal default profile with no factor. """
    inputs = Creds(username="user", password="secret", factor="")
    outputs = copy(inputs)
    outputs.factor = None

    def test_get_credentials(self):
        """ Should accept empty factor. """
        self._test_get_credentials()


class GetCredsMinProfileNoDuoTest(GetCredsProfileBase):
    """ Test minimal profile with duo disabled. """
    inputs = Creds(username="user", password="secret")
    outputs = copy(inputs)

    def setUp(self) -> None:
        super().setUp()
        self.login_config = """
[default]
ecp_endpoint_url = foo
factor = off
    """
        self.Profile()

    def test_get_credentials(self):
        """ Should prompt for just username/password. """
        self._test_get_credentials()


class GetCredsMinProfileTest(GetCredsProfileBase):
    """ Test minimal profile with factor passcode in profile. """
    inputs = Creds(username="user", password="secret", passcode="1234")
    outputs = copy(inputs)
    outputs.factor = 'passcode'

    def setUp(self) -> None:
        super().setUp()
        self.login_config = """
[default]
ecp_endpoint_url = foo
factor = passcode
    """
        self.Profile()

    def test_get_credentials(self):
        """ Should prompt for passcode with factor in profile. """
        self._test_get_credentials()


class GetCredsUsernameProfileTest(GetCredsProfileBase):
    """ Test profile with username in default profile """
    inputs = Creds(password="secret", factor="push")
    outputs = copy(inputs)
    outputs.username = "user"

    def setUp(self) -> None:
        super().setUp()
        self.login_config = """
[default]
ecp_endpoint_url = foo
username = user
    """
        self.Profile()

    def test_get_credentials(self):
        """ Should prompt for password/factor with username in profile. """
        self._test_get_credentials()


class GetCredsPasswordOnlyProfileTest(GetCredsProfileBase):
    """ Should only prompt for password with username/factor in profile """
    inputs = Creds(password="secret")

    outputs = copy(inputs)
    outputs.username = "user1"
    outputs.factor = "auto"

    def setUp(self) -> None:
        super().setUp()
        self.login_config = """
[default]
ecp_endpoint_url = foo
username = user1
factor = auto
    """
        self.Profile()

    def test_get_credentials(self):
        """ Should prompt for password only with username/factor in profile """
        self._test_get_credentials()


class GetCredsKeyringeTest(GetCredsProfileBase):
    """ Should not prompt for anyting """
    inputs = Creds(keyring="secret")

    outputs = copy(inputs)
    outputs.username = "user1"
    outputs.factor = "auto"
    outputs.password = "secret"

    def setUp(self) -> None:
        super().setUp()
        self.login_config = """
[default]
ecp_endpoint_url = foo
username = user1
factor = auto
enable_keyring = true
    """
        self.Profile()

    def test_get_credentials(self):
        """ Should not prompt with keyring/username/factor in profile """
        self._test_get_credentials()
