from copy import copy
from typing import List

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

    def mock_get_credentials_inputs(self, inputs: Creds):
        mock_input = self.patcher('builtins.input', autospec=True,
                                  side_effect=inputs.get())

        mock_password = self.patcher(
            'awscli_login.config.getpass',
            autospec=True,
            side_effect=[inputs.password]
        )

        mock_get_password = self.patcher(
            'awscli_login.config.get_password',
            autospec=True,
            side_effect=[inputs.keyring]
        )

        mock_set_password = self.patcher(
            'awscli_login.config.set_password',
            autospec=True
        )

        return (
            mock_input,
            mock_password,
            mock_get_password,
            mock_set_password,
            inputs,
        )

    def assertGetCredentialsMocksCalled(
            self,
            mock_input,
            mock_password,
            mock_get_password,
            mock_set_password,
            inputs,
    ):
        # Make sure the user was prompted for exactly the inputs given
        self.assertEqual(mock_input.call_count, len(inputs.get()))

        if inputs.password:
            try:  # Python 3.6 only
                mock_password.assert_called_once()
            except AttributeError:
                self.assertEqual(
                    1,
                    mock_password.call_count
                )
        else:
            try:  # Python 3.6 only
                mock_password.assert_not_called()
            except AttributeError:
                self.assertEqual(
                    0,
                    mock_password.call_count
                )

        if self.profile.enable_keyring:
            try:  # Python 3.6 only
                mock_get_password.assert_called_once()
                mock_set_password.assert_called_once()
            except AttributeError:
                self.assertEqual(
                    1,
                    mock_get_password.call_count
                )
                self.assertEqual(
                    1,
                    mock_set_password.call_count
                )
        else:
            try:
                mock_get_password.assert_not_called()
                mock_set_password.assert_not_called()
            except AttributeError:
                self.assertEqual(
                    0,
                    mock_get_password.call_count
                )
                self.assertEqual(
                    0,
                    mock_set_password.call_count
                )

    def _test_get_credentials(self, outputs: Creds) -> None:
        # Ensure actual outputs equal expected outputs
        errors = []
        mesg = 'get_credentials returned %s: %s. Expected: %s.'
        self.outputs = outputs

        usr, pwd, hdr = self.profile.get_credentials()

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


class GetCredsMinProfileBase(GetCredsProfileBase):
    """ Minimal default profile with no tests. """

    def setUp(self) -> None:
        super().setUp()
        self.login_config = """
[default]
ecp_endpoint_url = foo
    """
        self.Profile()

    def test_get_credentials_bad_factor(self):
        """ Given a bad factor on login InvalidFactor should be raised. """
        inputs = Creds(username="user", password="secret", factor="bozo")

        mocks = self.mock_get_credentials_inputs(inputs)
        with self.assertRaises(InvalidFactor):
            usr, pwd, hdr = self.profile.get_credentials()
        self.assertGetCredentialsMocksCalled(*mocks)

    def test_get_credentials_prompt_for_all(self):
        """ Should prompt for all user credentials. """
        inputs = Creds(username="user", password="secret", factor="passcode",
                       passcode="1234")
        outputs = copy(inputs)

        mocks = self.mock_get_credentials_inputs(inputs)
        self._test_get_credentials(outputs)
        self.assertGetCredentialsMocksCalled(*mocks)

    def test_get_credentials_phone_factor(self):
        """ Should accept phone factor. """
        inputs = Creds(username="user", password="secret", factor="phone")
        outputs = copy(inputs)

        mocks = self.mock_get_credentials_inputs(inputs)
        self._test_get_credentials(outputs)
        self.assertGetCredentialsMocksCalled(*mocks)

    def test_get_credentials_no_factor_given(self):
        """ Should accept empty factor. """
        inputs = Creds(username="user", password="secret", factor="")
        outputs = copy(inputs)
        outputs.factor = None

        mocks = self.mock_get_credentials_inputs(inputs)
        self._test_get_credentials(outputs)
        self.assertGetCredentialsMocksCalled(*mocks)


class GetCredsMinProfileNoDuoTest(GetCredsProfileBase):
    """ Test minimal profile with duo disabled. """

    def test_get_credentials_no_duo(self):
        """ Should prompt for just username/password. """
        self.login_config = """
[default]
ecp_endpoint_url = foo
factor = off
    """
        self.Profile()

        inputs = Creds(username="user", password="secret")
        outputs = copy(inputs)

        mocks = self.mock_get_credentials_inputs(inputs)
        self._test_get_credentials(outputs)
        self.assertGetCredentialsMocksCalled(*mocks)

    def test_get_credentials_prompt_for_passcode(self):
        """ Should prompt for passcode with factor in profile. """
        self.login_config = """
[default]
ecp_endpoint_url = foo
factor = passcode
    """
        self.Profile()

        inputs = Creds(username="user", password="secret", passcode="1234")
        outputs = copy(inputs)
        outputs.factor = 'passcode'

        mocks = self.mock_get_credentials_inputs(inputs)
        self._test_get_credentials(outputs)
        self.assertGetCredentialsMocksCalled(*mocks)

    def test_get_credentials_no_prompt_for_username(self):
        """ Should prompt for password/factor with username in profile. """
        self.login_config = """
[default]
ecp_endpoint_url = foo
username = user
    """
        self.Profile()

        inputs = Creds(password="secret", factor="push")
        outputs = copy(inputs)
        outputs.username = "user"

        mocks = self.mock_get_credentials_inputs(inputs)
        self._test_get_credentials(outputs)
        self.assertGetCredentialsMocksCalled(*mocks)

    def test_get_credentials_password_only(self):
        """ Should prompt for password only with username/factor in profile """
        self.login_config = """
[default]
ecp_endpoint_url = foo
username = user1
factor = auto
    """
        self.Profile()

        inputs = Creds(password="secret")

        outputs = copy(inputs)
        outputs.username = "user1"
        outputs.factor = "auto"

        mocks = self.mock_get_credentials_inputs(inputs)
        self._test_get_credentials(outputs)
        self.assertGetCredentialsMocksCalled(*mocks)

    def test_get_credentials_keyring_test_no_prompt(self):
        """ Should not prompt with keyring/username/factor in profile """
        self.login_config = """
[default]
ecp_endpoint_url = foo
username = user1
factor = auto
enable_keyring = true
    """
        self.Profile()

        inputs = Creds(keyring="secret")

        outputs = copy(inputs)
        outputs.username = "user1"
        outputs.factor = "auto"
        outputs.password = "secret"

        mocks = self.mock_get_credentials_inputs(inputs)
        self._test_get_credentials(outputs)
        self.assertGetCredentialsMocksCalled(*mocks)
