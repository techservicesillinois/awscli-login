import unittest

from argparse import Namespace
from functools import partial
from unittest.mock import call, patch

from awscli_login.account_names import _edit_account_names, xargs_handler
from .login import Login

TEST_CASE_1_ROLES = [
    ('arn:aws:iam::765432109876:saml-provider/foo.com',
     'arn:aws:iam::765432109876:role/abc'),
    ('arn:aws:iam::321098765432:saml-provider/foo.com',
     'arn:aws:iam::321098765432:role/def'),
    ('arn:aws:iam::543210987654:saml-provider/foo.com',
     'arn:aws:iam::543210987654:role/ghi'),
    ('arn:aws:iam::109876543210:saml-provider/foo.com',
     'arn:aws:iam::109876543210:role/jkl'),
    ('arn:aws:iam::654321098765:saml-provider/foo.com',
     'arn:aws:iam::654321098765:role/mno'),
    ('arn:aws:iam::210987654321:saml-provider/foo.com',
     'arn:aws:iam::210987654321:role/pqr'),
]

TEST_CASE_1_ALIASES = {
    '765432109876': 'abc',
    '321098765432': 'def',
    '543210987654': 'ghi',
    '109876543210': 'jkl',
    '654321098765': 'mno',
    '210987654321': 'pqr',
}

TEST_CASE_1_EXISTING = {
    '765432109876': 'ABC',
    '321098765432': 'DEF',
    '543210987654': 'GHI',
    '109876543210': 'JKL',
    '654321098765': 'MNO',
    '210987654321': 'PQR',
}

TEST_CASE_2_ROLES = [
    ('arn:aws:iam::765432109876:saml-provider/foo.com',
     'arn:aws:iam::765432109876:role/abc'),
    ('arn:aws:iam::765432109876:saml-provider/foo.com',
     'arn:aws:iam::765432109876:role/def'),
]


class MockIAMClient():
    def __init__(self, alias=None):
        self.alias = alias

    def list_account_aliases(self):
        if self.alias:
            return {'AccountAliases': [self.alias]}
        else:
            return {}


class MockBotocoreClient():
    def assume_role_with_saml(*args, **kwargs):
        account_id = kwargs["RoleArn"].split(':')[4]
        return {'Credentials': {
                    'AccessKeyId': account_id,
                    'SecretAccessKey': 'FAKE_ACCESS_KEY',
                    'SessionToken': '"FAKE_TOKEN',
            }
        }


def create_client_mock(alias, service, **kwargs):
    if service == 'iam':
        key = kwargs["aws_access_key_id"]
        return MockIAMClient(None if alias is None else alias[key])
    else:
        return MockBotocoreClient()


class TestLoginAccountName(Login):
    """ Integration tests for no profile. """
    profile = None  # default

    @patch('awscli_login.account_names.input', return_value='')
    @patch("awscli_login.account_names.refresh",
           return_value=("SAML", TEST_CASE_1_ROLES))
    def test_acct_select_prexisting_value(self, mock_refresh, mock_input):
        """ Set account names to prexisting values using return key. """
        self.profile.account_names = TEST_CASE_1_EXISTING
        self.session.create_client = partial(create_client_mock,
                                             TEST_CASE_1_ALIASES)

        ret = _edit_account_names(self.profile, self.session,
                                  Namespace(auto=False))

        self.assertEqual(ret, TEST_CASE_1_EXISTING)

        calls = [call(f"{acct_id} [{alias}]: ") for acct_id, alias in
                 TEST_CASE_1_EXISTING.items()]
        mock_input.assert_has_calls(calls, any_order=True)
        self.assertEqual(len(mock_input.call_args_list), len(calls))

    @patch('awscli_login.account_names.input', return_value='')
    @patch("awscli_login.account_names.refresh",
           return_value=("SAML", TEST_CASE_1_ROLES))
    def test_acct_select_default(self, mock_refresh, mock_input):
        """ Set account names to default values using return key. """
        self.session.create_client = partial(create_client_mock,
                                             TEST_CASE_1_ALIASES)

        ret = _edit_account_names(self.profile, self.session,
                                  Namespace(auto=False))

        self.assertEqual(ret, TEST_CASE_1_ALIASES)

        calls = [call(f"{acct_id} [{alias}]: ") for acct_id, alias in
                 TEST_CASE_1_ALIASES.items()]
        mock_input.assert_has_calls(calls, any_order=True)
        self.assertEqual(len(mock_input.call_args_list), len(calls))

    @patch('awscli_login.account_names.input', return_value='')
    @patch("awscli_login.account_names.refresh",
           return_value=("SAML", TEST_CASE_1_ROLES))
    def test_acct_select_default_auto(self, mock_refresh, mock_input):
        """ Set account names to default values automatically. """
        self.session.create_client = partial(create_client_mock,
                                             TEST_CASE_1_ALIASES)

        ret = _edit_account_names(self.profile, self.session,
                                  Namespace(auto=True))

        self.assertEqual(ret, TEST_CASE_1_ALIASES)
        self.assertEqual(len(mock_input.call_args_list), 0)

    @patch('awscli_login.account_names.input', return_value='')
    @patch("awscli_login.account_names.refresh",
           return_value=("SAML", TEST_CASE_1_ROLES))
    def test_acct_select_default_no_alias(self, mock_refresh, mock_input):
        """ Account names w/o an AWS alias are not set by the user. """
        self.session.create_client = partial(create_client_mock, None)

        ret = _edit_account_names(self.profile, self.session,
                                  Namespace(auto=False))

        self.assertEqual(ret, {})

        calls = [call(f"{acct_id} [None]: ") for acct_id in
                 TEST_CASE_1_ALIASES.keys()]
        mock_input.assert_has_calls(calls, any_order=True)
        self.assertEqual(len(mock_input.call_args_list), len(calls))

    @patch('awscli_login.account_names.input', return_value="foo")
    @patch("awscli_login.account_names.refresh",
           return_value=("SAML", TEST_CASE_1_ROLES))
    def test_acct_name_change_value(self, mock_refresh, mock_input):
        """ Set account names to user supplied value. """
        self.session.create_client = partial(create_client_mock,
                                             TEST_CASE_1_ALIASES)

        ret = _edit_account_names(self.profile, self.session,
                                  Namespace(auto=False))

        new_alias_values = {f"{acct_id}": "foo" for acct_id, _ in
                            TEST_CASE_1_ALIASES.items()}
        self.assertEqual(ret, new_alias_values)

        calls = [call(f"{acct_id} [{alias}]: ") for acct_id, alias in
                 TEST_CASE_1_ALIASES.items()]
        mock_input.assert_has_calls(calls, any_order=True)
        self.assertEqual(len(mock_input.call_args_list), len(calls))

    @patch('awscli_login.account_names.input', return_value="foo")
    @patch("awscli_login.account_names.refresh",
           return_value=("SAML", TEST_CASE_1_ROLES))
    def test_acct_no_aws_alias(self, mock_refresh, mock_input):
        """ Set account names w/o an AWS alias to user supplied value. """
        self.session.create_client = partial(create_client_mock, None)

        ret = _edit_account_names(self.profile, self.session,
                                  Namespace(auto=False))

        new_alias_values = {f"{acct_id}": "foo" for acct_id, _ in
                            TEST_CASE_1_ALIASES.items()}
        self.assertEqual(ret, new_alias_values)

        calls = [call(f"{acct_id} [None]: ") for acct_id in
                 TEST_CASE_1_ALIASES.keys()]
        mock_input.assert_has_calls(calls, any_order=True)
        self.assertEqual(len(mock_input.call_args_list), len(calls))

    @patch('awscli_login.account_names.input', side_effect=["foo", "bar"])
    @patch("awscli_login.account_names.refresh",
           return_value=("SAML", TEST_CASE_2_ROLES))
    def test_acct_dont_ask_twice(self, mock_refresh, mock_input):
        """ Ask for an alias once for each unique account. """
        self.session.create_client = partial(create_client_mock,
                                             {'765432109876': 'abc'})

        ret = _edit_account_names(self.profile, self.session,
                                  Namespace(auto=False))

        self.assertEqual(ret, {'765432109876': 'foo'})

        mock_input.assert_called_once_with("765432109876 [abc]: ")
        self.assertEqual(len(mock_input.call_args_list), 1)


class TestXargs(unittest.TestCase):
    def test_xargs(self):
        args = Namespace(foo="bar", auto=True)

        nargs = xargs_handler(args)
        self.assertEqual(args, Namespace(foo="bar"))
        self.assertEqual(nargs, Namespace(auto=True))
