import unittest

from unittest.mock import (
    MagicMock,
    patch,
)

from awscli_login.__main__ import (
    login,
    save_sts_token,
)


class MockProfile():
    role_arn = "RoleArn"
    cookies = "MockCookies"
    duration = 0
    ecp_endpoint_url = "http://127.0.0.1"
    force_refresh = False
    name = 'default'
    verify_ssl_certificate = True

    def raise_if_logged_in(self):
        return


class MockBotocoreClient():
    pass


class saveStsToken(unittest.TestCase):

    def setUp(self):
        self.profile = MockProfile()
        self.client = MockBotocoreClient()

        self.saml = "MockSAMLAssertion"
        self.role = ["PrincipalArn", "RoleArn"]
        self.token = "MockedToken"

        self.client.assume_role_with_saml = MagicMock(return_value=self.token)
        self.profile.save_credentials = MagicMock()

    def test_save_sts_token(self):
        """ save_sts_token should save and return a token """
        token = save_sts_token(self.profile, self.client, self.saml, self.role)

        self.assertEqual(token, self.token)
        self.client.assume_role_with_saml.assert_called_with(
            PrincipalArn=self.role[0],
            RoleArn=self.role[1],
            SAMLAssertion=self.saml,
        )
        self.profile.save_credentials.assert_called_with(self.token, self.role)

    def test_save_sts_token_duration(self):
        """ save_sts_token with duration should return time limited creds. """
        seconds = 100
        token = save_sts_token(self.profile, self.client, self.saml, self.role,
                               duration=seconds)

        self.assertEqual(token, self.token)
        self.client.assume_role_with_saml.assert_called_with(
            PrincipalArn=self.role[0],
            RoleArn=self.role[1],
            SAMLAssertion=self.saml,
            DurationSeconds=seconds,
        )
        self.profile.save_credentials.assert_called_with(self.token, self.role)


class Login(unittest.TestCase):

    def setUp(self):
        self.profile = MockProfile()
        self.session = MockBotocoreClient()
        self.client = MockBotocoreClient()

        self.profile.raise_if_logged_in = MagicMock()
        self.profile.get_username = MagicMock()
        self.profile.get_credentials = MagicMock()

        self.session.set_credentials = MagicMock()
        self.session.create_client = MagicMock(return_value=self.client)

    @patch("awscli_login.__main__.authenticate",
           return_value=("SAML", ["PrincipalArn", "RoleArn"]))
    @patch("awscli_login.__main__.save_sts_token")
    @patch("awscli_login.__main__.get_selection",
           return_value=["PrincipalArn2", "RoleArn2"])
    @patch("awscli_login.__main__.refresh", side_effect=Exception("W00T!"))
    def test_interactive_login(
            self, refresh, get_selection, save_sts_token, authenticate):
        """ Interactive login wo/refreshable creds should prompt user. """
        login(self.profile, self.session, interactive=True)
        self.session.set_credentials.assert_called_with(None, None)
        self.session.create_client.assert_called_with("sts")

        self.profile.get_username.assert_called()
        refresh.assert_called_with(
            self.profile.ecp_endpoint_url,
            self.profile.cookies,
            self.profile.verify_ssl_certificate,
        )
        self.profile.get_credentials.assert_called()
        authenticate.assert_called_with(
            self.profile.ecp_endpoint_url,
            self.profile.cookies,
            self.profile.verify_ssl_certificate,
        )
        get_selection.assert_called_with(["PrincipalArn", "RoleArn"],
                                         self.profile.role_arn, True)
        save_sts_token.assert_called_with(
            self.profile,
            self.client,
            "SAML",
            ["PrincipalArn2", "RoleArn2"],
            self.profile.duration
        )

    @patch("awscli_login.__main__.authenticate")
    @patch("awscli_login.__main__.save_sts_token")
    @patch("awscli_login.__main__.get_selection",
           return_value=["PrincipalArn2", "RoleArn2"])
    @patch("awscli_login.__main__.refresh",
           return_value=("SAML", ["PrincipalArn", "RoleArn"]))
    def test_interactive_refresh_login(
            self, refresh, get_selection, save_sts_token, authenticate):
        """ Interactive login w/refreshable creds should not prompt user. """
        login(self.profile, self.session, interactive=True)
        self.session.set_credentials.assert_called_with(None, None)
        self.session.create_client.assert_called_with("sts")

        self.profile.get_username.assert_called()
        refresh.assert_called_with(
            self.profile.ecp_endpoint_url,
            self.profile.cookies,
            self.profile.verify_ssl_certificate,
        )
        self.profile.get_credentials.assert_not_called()
        authenticate.assert_not_called()
        get_selection.assert_called_with(["PrincipalArn", "RoleArn"],
                                         self.profile.role_arn, True)
        save_sts_token.assert_called_with(
            self.profile,
            self.client,
            "SAML",
            ["PrincipalArn2", "RoleArn2"],
            self.profile.duration
        )

    @patch("awscli_login.__main__.authenticate")
    @patch("awscli_login.__main__.save_sts_token")
    @patch("awscli_login.__main__.get_selection",
           return_value=["PrincipalArn2", "RoleArn2"])
    @patch("awscli_login.__main__.refresh",
           return_value=("SAML", ["PrincipalArn", "RoleArn"]))
    def test_noninteractive_login(
            self, refresh, get_selection, save_sts_token, authenticate):
        """ A non interactive login should not prompt the user. """
        login(self.profile, self.session, interactive=False)
        self.session.set_credentials.assert_called_with(None, None)
        self.session.create_client.assert_called_with("sts")

        self.profile.get_username.assert_not_called()
        refresh.assert_called_with(
            self.profile.ecp_endpoint_url,
            self.profile.cookies,
            self.profile.verify_ssl_certificate,
        )
        self.profile.get_credentials.assert_not_called()
        authenticate.assert_not_called()
        get_selection.assert_called_with(["PrincipalArn", "RoleArn"],
                                         self.profile.role_arn, False)
        save_sts_token.assert_called_with(
            self.profile,
            self.client,
            "SAML",
            ["PrincipalArn2", "RoleArn2"],
            self.profile.duration
        )
