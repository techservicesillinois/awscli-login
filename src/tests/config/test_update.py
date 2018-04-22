""" Tests for profile.update the backend for aws configure login """
from os.path import getmtime, relpath
from time import sleep
from typing import Any, Dict
from unittest.mock import patch

from .base import ProfileBase
from .util import user_input


class UpdateProfileBase(ProfileBase):
    expected_attr_vals: Dict[str, Any] = {}

    def _test_profile_update(self, no_change=False) -> None:
        """ Simulate user configuration of default profile. """
        self.Profile()
        self.usr_input = user_input(self.profile, self.expected_attr_vals)

        patcher = patch(
            'builtins.input',
            side_effect=self.usr_input,
        )
        self.mock = patcher.start()
        self.addCleanup(patcher.stop)

        # We must sleep otherwise old == new!
        sleep(1)

        old = getmtime(self.login_config_path)
        self.profile.update()
        new = getmtime(self.login_config_path)

        if no_change:
            self.assertEqual(
                new, old, 'Error: file %s was touched!' %
                relpath(self.login_config_path, self.tmpd.name)
            )
        else:
            self.assertGreater(
                new, old, 'Error: file %s was not touched!' %
                relpath(self.login_config_path, self.tmpd.name)
            )

        self.profile.reload()
        try:
            self.assertProfileHasAttrs(**self.expected_attr_vals)
        except AssertionError as e:
            mesg = "\n\nUser input: " + ', '.join(self.usr_input) + '\n'
            mesg += "\nConfig file on disk: \n"
            with open(self.profile.config_file, 'r') as f:
                mesg += f.read()

            e.args = (e.args[0] + mesg, )
            raise e


class UpdateDefaultProfileTest(UpdateProfileBase):
    """ Test updating the default profile configuration """
    expected_attr_vals = {
        "ecp_endpoint_url": 'url2',
        "username": 'netid2',
        "enable_keyring": False,
        "role_arn": "arn:aws:iam::account-id:role/role-name2",
        "factor": 'auto',
    }

    def setUp(self) -> None:
        super().setUp()
        self.login_config = """
[default]
ecp_endpoint_url = url
username = netid1
enable_keyring = True
role_arn = arn:aws:iam::account-id:role/role-name
factor = push
    """

    def test_profile_update(self) -> None:
        """ Simulate user configuration of default profile. """
        self._test_profile_update()


class UpdateDefaultProfileNoChangeTest(UpdateDefaultProfileTest):
    """ Test making no changes with profile.update to default profile. """
    expected_attr_vals: Dict[str, Any] = {}

    def test_profile_update(self) -> None:
        """ Simulate user making no changes with configuration tool. """
        self._test_profile_update(no_change=True)


class UpdateNonDefaultProfileTest(UpdateDefaultProfileTest):
    profile_name = "test"

    def setUp(self):
        super().setUp()
        self.login_config = self.login_config.replace(
            'default',
            self.profile_name
        )

    def test_profile_update(self) -> None:
        """ Simulate user configuration of non-default profile. """
        self._test_profile_update()
