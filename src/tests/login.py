import unittest

from unittest.mock import (
    MagicMock,
)

from typing import Dict


class MockProfile():
    role_arn = "RoleArn"
    cookies = "MockCookies"
    duration = 0
    ecp_endpoint_url = "http://127.0.0.1"
    force_refresh = False
    name = 'default'
    verify_ssl_certificate = True
    account_names: Dict[str, str] = {}

    def raise_if_logged_in(self):
        return

    def raise_if_logged_out(self):
        return

    def write_identity_files(self, role):
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
