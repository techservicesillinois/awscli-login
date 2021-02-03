from copy import copy
from typing import List, Iterator

from awscli_login.const import (
    DUO_HEADER_FACTOR,
    DUO_HEADER_PASSCODE,
)
from awscli_login.exceptions import InvalidFactor

from .base import ProfileBase


class Creds():

    def __init__(self, username: str = None, password: str = None,
                 factor: str = None, passcode: str = None,
                 keyring: str = None) -> None:
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

    def input(self) -> Iterator[str]:
        i = 0
        r = self.get()

        while True:
            try:
                yield r[i]
                i += 1
            except IndexError:
                yield ''


class GetCredsProfileBase(ProfileBase):

    def mock_get_credentials_inputs(self, inputs: Creds):
        mock_input = self.patcher('builtins.input', autospec=True,
                                  side_effect=inputs.input())

        mock_password = self.patcher(
            'awscli_login.config.getpass',
            autospec=True,
            # getpass should always return a string value!
            side_effect=[inputs.password if inputs.password else '']
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
        self.assertEqual(
            mock_input.call_count, len(inputs.get()),
            "%i user prompt(s) expected!" % len(inputs.get()),
        )

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
        usr, pwd, hdr = self.profile.get_credentials()

        self._test_get_credentials_outputs(usr, pwd, hdr, outputs)

    def _test_get_credentials_outputs(self, usr, pwd, hdr,
                                      outputs: Creds) -> None:

        # Ensure actual outputs equal expected outputs
        errors = []
        mesg = 'get_credentials returned %s: %s. Expected: %s.'
        self.outputs = outputs

        pairs = [
            ('username', usr),
            ('password', pwd),
            ('factor', hdr.get(DUO_HEADER_FACTOR)),
            ('passcode', hdr.get(DUO_HEADER_PASSCODE)),
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

    def test_get_credentials_no_prompt_for_passcode(self):
        """ Should not prompt for passcode when set in profile. """
        self.login_config = """
[default]
ecp_endpoint_url = foo
factor = passcode
passcode = abcd
    """
        self.Profile()

        inputs = Creds(username="user", password="secret")
        outputs = copy(inputs)
        outputs.factor = 'passcode'
        outputs.passcode = 'abcd'

        mocks = self.mock_get_credentials_inputs(inputs)
        self._test_get_credentials(outputs)
        self.assertGetCredentialsMocksCalled(*mocks)

    def test_get_credentials_no_prompt_for_cli_passcode(self):
        """ Should not prompt for passcode when set on command line. """
        self.login_config = """
[default]
ecp_endpoint_url = foo
factor = passcode
    """
        self.Profile(passcode='abcd')

        inputs = Creds(username="user", password="secret")
        outputs = copy(inputs)
        outputs.factor = 'passcode'
        outputs.passcode = 'abcd'

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


class GetCredsWithArgsMinProfileTest(GetCredsProfileBase):
    """ Test that cli arguments are able to override profile settings
    and prevent the user from being prompted for the value set. """

    def _test_clioverrides_profile(self, inputs: Creds, outputs: Creds,
                                   **kwargs):
        """ Test that get_credentials_inputs returns given outputs
        when supplied with mocked user inputs.

        inputs: Values used to mock user input.
        outputs: Expected values set on profile after get_credentials is
                 called with mocked inputs.
        kwargs: Command line arguments passed to user profile.

        """
        # Pass cli arguments
        self.Profile(**kwargs)

        # Call get_credentials with mocked input
        mocks = self.mock_get_credentials_inputs(inputs)
        usr, pwd, hdr = self.profile.get_credentials()

        # Ensure that only expected values asked for
        self.assertGetCredentialsMocksCalled(*mocks)

        # Ensure that values returned match expected values
        self._test_get_credentials_outputs(usr, pwd, hdr, outputs)

    def test_get_credentials_password_arg_set(self):
        """ Prompt for just username when password cli flag is set. """
        self.login_config = """
[default]
ecp_endpoint_url = foo
factor = off
    """
        pwd = "1234"
        inputs = Creds(username="user")
        outputs = Creds(username="user", password=pwd)

        self._test_clioverrides_profile(inputs, outputs, password=pwd)

    def test_get_credentials_username_password_set_in_config(self):
        """ Prompt for nothing when username & password properties are set. """
        self.login_config = """
[default]
ecp_endpoint_url = foo
factor = off
password = 1234
username = foo
    """
        inputs = Creds()
        outputs = Creds(username="foo", password="1234")

        self._test_clioverrides_profile(inputs, outputs)

    def test_get_credentials_use_keyring_instead_of_property(self):
        """ Use keyring even if password property is set. """
        self.login_config = """
[default]
ecp_endpoint_url = foo
enable_keyring = True
factor = off
password = 1234
username = foo
    """
        inputs = Creds(keyring="secret")
        outputs = Creds(username="foo", password="secret")

        self._test_clioverrides_profile(inputs, outputs)

    def test_get_credentials_use_keyring_instead_of_flag(self):
        """ Use keyring even if password flag is set. """
        self.login_config = """
[default]
ecp_endpoint_url = foo
enable_keyring = True
factor = off
username = foo
    """
        inputs = Creds(keyring="secret")
        outputs = Creds(username="foo", password="secret")

        self._test_clioverrides_profile(inputs, outputs)
