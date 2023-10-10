import json

from datetime import datetime
from io import StringIO
from unittest.mock import patch
from unittest import TestCase

from awscli_login.credentials import print_credentials


class TestCredentials(TestCase):
    @patch('sys.stderr', new_callable=StringIO)
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_credentials(self, out, err):
        expiration = "2022-07-11T20:14:04+00:00"
        token = {
            'Credentials': {
                "AccessKeyId": "SUPERCOOLACCESKEYID",
                "SecretAccessKey": "1234567890",
                "SessionToken": "asdfghjkl;",
                "Expiration": datetime.fromisoformat(expiration)
            }
        }
        expected = token['Credentials'].copy()
        expected['Expiration'] = expiration
        expected['Version'] = 1

        print_credentials(token)
        output = json.loads(out.getvalue())

        assert "Version" in output
        assert "AccessKeyId" in output
        assert "SecretAccessKey" in output
        assert "SessionToken" in output
        assert "Expiration" in output
        assert len(output) == 5
        assert output == expected
        assert err.getvalue() == ''
