""" Tests for profile.update the backend for aws configure login """
# from os.path import getmtime, relpath
# from time import sleep
from typing import Any
from unittest.mock import patch

from .base import ProfileBase
from .util import user_input


class UpdateProfileBase(ProfileBase):

    def assertProfileHasAttrsAfterUpdate(self, no_change=False,
                                         **kwargs: Any) -> None:
        """ Simulate user configuration of default profile. """
        usr_input = user_input(self.profile, kwargs)

        @patch('builtins.input', side_effect=usr_input)
        def profileUpdate(mock):
            self.profile.update()

        if no_change:
            self.assertTmpFileNotChangedBy(
                self.login_config_path,
                profileUpdate,
            )
        else:
            self.assertTmpFileChangedBy(
                self.login_config_path,
                profileUpdate,
            )

        self.profile.reload()
        try:
            self.assertProfileHasAttrs(**kwargs)
        except AssertionError as e:
            mesg = "\n\nUser input: " + ', '.join(usr_input) + '\n'
            mesg += "\nConfig file on disk: \n"
            with open(self.profile.config_file, 'r') as f:
                mesg += f.read()

            e.args = (e.args[0] + mesg, )
            raise e


class UpdateDefaultProfileTest(UpdateProfileBase):
    """ Test updating the default profile configuration """

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
        """Simulate user configuration of default profile. """
        self.Profile()
        self.assertProfileHasAttrsAfterUpdate(
            ecp_endpoint_url='url2',
            username='netid2',
            enable_keyring=False,
            role_arn="arn:aws:iam::account-id:role/role-name2",
            factor='auto',
        )

    def test_profile_update_no_change(self) -> None:
        """Simulate user making no changes with configuration tool. """
        self.Profile()
        self.assertProfileHasAttrsAfterUpdate(no_change=True)

    def test_non_default_profile_update(self) -> None:
        """Simulate user configuration of default profile. """
        self.login_config = self.login_config.replace(
            'default',
            'test'
        )

        self.Profile('test')
        self.assertProfileHasAttrsAfterUpdate(
            ecp_endpoint_url='url2',
            username='netid2',
            enable_keyring=False,
            role_arn="arn:aws:iam::account-id:role/role-name2",
            factor='auto',
        )

    def test_non_default_profile_update_no_change(self) -> None:
        """ Simulate user making no changes to non-default profile. """
        self.login_config = self.login_config.replace(
            'default',
            'test'
        )

        self.Profile('test')
        self.assertProfileHasAttrsAfterUpdate(no_change=True)
