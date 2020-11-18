import requests
import tempfile
import unittest

from datetime import datetime
from os import path
from os.path import dirname, abspath
from requests.exceptions import HTTPError
from unittest.mock import patch, MagicMock

from lxml.etree import XMLSyntaxError

from awscli_login.saml import (
    authenticate,
    authn_request,
    parse_role_arns,
    parse_soap_response,
    refresh,
    raise_if_saml_failed,
)

from awscli_login.exceptions import (
    AuthnFailed,
    InvalidSOAP,
    MissingCookieJar,
    RoleParseFail,
)
from awscli_login.util import (
    file2str,
    file2bytes,
)

DATA = path.join(dirname(abspath(__file__)), 'data')

ARN = 'arn:aws:iam::378517677616:'
SAML_SUCCESS = file2bytes(path.join(DATA, 'success.xml'))
SAML_SUCCESS_ARNS = [(
    ARN + 'saml-provider/shibboleth-test.techservices.illinois.edu',
    ARN + 'role/TestShibAdmin'
)]

SAML_SUCCESS_B64 = file2str(path.join(DATA, 'success.b64'))
SAML_AUTHNFAILED = file2bytes(path.join(DATA, 'error.xml'))
SAML_AUTHNFAILED_HTML = file2bytes(path.join(DATA, 'error.html'))
AUTHNREQUEST = file2bytes(path.join(DATA, 'authnrequest.xml'))


class saml(unittest.TestCase):
    """ Tests various SAML helper functions """
    maxDiff = None

    def test_saml_authnfailed(self):
        """ raise_if_saml_failed should raise an error if AuthNfailed. """
        with self.assertRaises(AuthnFailed):
            raise_if_saml_failed(SAML_AUTHNFAILED)

    def test_saml_bad_soap(self):
        """ raise_if_saml_failed should raise an error if HTML is given. """
        with self.assertRaises(XMLSyntaxError):
            raise_if_saml_failed(SAML_AUTHNFAILED_HTML)

    def test_saml_success(self):
        """ raise_if_saml_failed should not raise an error on success. """
        raise_if_saml_failed(SAML_SUCCESS)

    @patch('awscli_login.saml.utcnow',
           return_value=datetime(2018, 4, 5, 16, 6, 50))
    @patch('awscli_login.saml.uuid4',
           return_value='37435E75-D889-45F3-A8EC-FD538C1F6BCC')
    def test_authn_request(self, *args):
        """ authn_request should return expected output with static inputs. """
        self.assertEqual(authn_request(), AUTHNREQUEST)

    def test_parse_soap_response(self):
        """ Given a SAML response PSR should return roles and assertion. """
        assertion, arns = parse_soap_response(SAML_SUCCESS)

        self.assertEqual(assertion, SAML_SUCCESS_B64)
        self.assertEqual(arns, SAML_SUCCESS_ARNS)

    def test_parse_role_arns(self):
        """ Given bad soap PRA should throw a SAML exception. """
        class role:
            text = 'bad role'

        with self.assertRaises(RoleParseFail):
            parse_role_arns([role(), role()])


class auth(unittest.TestCase):
    """ Tests for saml.authenticate and saml.refresh. """
    maxDiff = None

    class MockRespone:
        """ A class for mocking a requests' response. """
        status_code = 0  # type: int
        content = None  # type: bytes

        def raise_for_status(self):
            pass

    class Success(MockRespone):
        status_code = 200
        content = SAML_SUCCESS

    class Failure401(MockRespone):
        status_code = 401
        content = SAML_AUTHNFAILED_HTML

        def raise_for_status(self):
            raise HTTPError()

    class FailureSoap(MockRespone):
        status_code = 200
        content = SAML_AUTHNFAILED

    class BadSoap(MockRespone):
        status_code = 200
        content = SAML_AUTHNFAILED_HTML

    def auth(self, cookies: str):
        """ Wrapper for calling saml.authenticate. """
        return authenticate(
            self.URL,
            cookies,  # TODO FIXME
            username='netid',
            password='password',
            headers={},
        )

    def refresh(self, cookies: str):
        """ Wrapper for calling saml.refresh. """
        return refresh(
            self.URL,
            cookies,
        )

    def setUp(self):
        idphost = "shibboleth-test.techservices.illinois.edu"

        self.URL = "https://" + idphost + "/idp/profile/SAML2/SOAP/ECP"
        self.cookies = 'cookies.txt'

    @patch('awscli_login.saml.Session')
    def auth_test(self, returns, saml, roles, test_func, mock,
                  create_cookies=False):
        """
        Helper function for testing saml authenticate & refresh.

        Tests that test_func returns the expected output.

        Args:
            returns (list): MockRespone(s) to be returned by requests.post.
            saml (str): Expected base 64 SAML assertion to be returned by
                        test_func.
            roles (Role): Expected roles to be returned by test_func.
            test_func: either self.auth or self.refresh.
        """
        mock.return_value = requests.Session()
        mock.return_value.post = MagicMock(side_effect=returns)

        with tempfile.TemporaryDirectory() as tempdir:
            cookies = path.join(tempdir, 'cookies.txt')
            if create_cookies:
                with open(cookies, 'w') as f:
                    f.write('#LWP-Cookies-2.0')

            encoded, arns = test_func(cookies)

        self.assertEqual(encoded, saml)
        self.assertEqual(arns, roles)

    def test_authenticate_with_username_password(self):
        """ Simulates successful auth with username/password. """
        idp = [self.Success()]
        self.auth_test(idp, SAML_SUCCESS_B64, SAML_SUCCESS_ARNS,
                       self.auth)

    def test_authenticate_bad_login_401(self):
        """ Simulates a failed user login. IdP returns 401 error. """
        idp = [self.Failure401()]

        with self.assertRaises(HTTPError):
            self.auth_test(idp, "", {}, self.auth)

    def test_authenticate_bad_login_soap(self):
        """ Simulates a failed user login. IdP returns soap error. """
        idp = [self.FailureSoap()]

        with self.assertRaises(AuthnFailed):
            self.auth_test(idp, "", {}, self.auth)

    def test_authenticate_bad_soap(self):
        """ Simulates a bad ECP endpoint that returns junk on auth. """
        idp = [self.BadSoap()]

        with self.assertRaises(InvalidSOAP):
            self.auth_test(idp, "", {}, self.auth)

    def test_refresh_with_cookies(self):
        """ Simulates successful refresh with cookies. """
        idp = [self.Success()]
        self.auth_test(idp, SAML_SUCCESS_B64, SAML_SUCCESS_ARNS, self.refresh,
                       create_cookies=True)

    def test_refresh_bad_login_401(self):
        """ Simulates failed refresh with cookies. IdP returns 401 error. """
        idp = [self.Failure401()]

        with self.assertRaises(HTTPError):
            self.auth_test(idp, "", {}, self.refresh, create_cookies=True)

    def test_refresh_bad_login_soap(self):
        """ Simulates failed refresh with cookies. IdP returns soap error. """
        idp = [self.FailureSoap()]

        with self.assertRaises(AuthnFailed):
            self.auth_test(idp, "", {}, self.refresh, create_cookies=True)

    def test_refresh_bad_soap(self):
        """ Simulates a bad ECP endpoint that returns junk on refresh. """
        idp = [self.BadSoap()]

        with self.assertRaises(InvalidSOAP):
            self.auth_test(idp, "", {}, self.refresh, create_cookies=True)

    def test_refresh_no_cookie_jar(self):
        """ Simulates a no cookie jar found error on refresh. """
        idp = [self.FailureSoap()]

        with self.assertRaises(MissingCookieJar):
            self.auth_test(idp, "", {}, self.refresh, create_cookies=False)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    unittest.main()
