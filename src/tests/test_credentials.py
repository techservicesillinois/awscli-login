from unittest.mock import (
    MagicMock,
    patch,
)

from awscli_login.credentials import (
    get_credentials,
)

from .login import Login


class awsLoginTests(Login):
    """ Class to test the aws-login script. """

    # NOTA BENE: This is a regression test for issue #257
    @patch("awscli_login.credentials.print_credentials")
    @patch("awscli_login.__main__.authenticate")
    @patch("awscli_login.__main__.save_sts_token")
    @patch("awscli_login.__main__.get_selection",
           return_value=["PrincipalArn2", "RoleArn2"])
    @patch("awscli_login.__main__.refresh",
           return_value=("SAML", ["PrincipalArn", "RoleArn"]))
    def test_get_credentials_with_refresh(
            self, refresh, get_selection, save_sts_token, authenticate,
            print_credentials):
        """ get_credentials should refresh expired credentials. """
        fake_token = {"TOKEN": "FAKE_DATA"}
        self.profile.are_credentials_expired = MagicMock(return_value=True)
        save_sts_token.return_value = fake_token
        self.profile.load_credentials = MagicMock(return_value=fake_token)

        get_credentials(self.profile, self.session)

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
                                         self.profile.role_arn, False, {})
        save_sts_token.assert_called_with(
            self.profile,
            self.client,
            "SAML",
            ["PrincipalArn2", "RoleArn2"],
            self.profile.duration
        )
        self.profile.load_credentials.assert_not_called()
        print_credentials.assert_called_with(fake_token)

    @patch("awscli_login.credentials.print_credentials")
    @patch("awscli_login.credentials.login")
    def test_get_credentials_without_refresh(
            self, login, print_credentials):
        """ get_credentials should just print current credentials. """
        fake_token = {"TOKEN": "FAKE_DATA"}
        self.profile.are_credentials_expired = MagicMock(return_value=False)
        self.profile.load_credentials = MagicMock(return_value=fake_token)

        get_credentials(self.profile, self.session)

        login.assert_not_called()
        self.profile.load_credentials.assert_called()
        print_credentials.assert_called_with(fake_token)
