from .base import ProfileBase


class IsFactorPromptDisabled(ProfileBase):
    """
    Tests that profile.is_factor_prompt_disabled and
    profile.is_factor_valid work as expected
    """

    def setUp(self) -> None:
        super().setUp()
        self.login_config = """
[default]
ecp_endpoint_url = foo
    """
        self.Profile()

    # Profile.is_factor_prompt_disabled() tests

    def test_factor_none(self):
        "Factor prompt should be enabled when no factor is given. """
        # self.profile.factor = None
        self.assertFalse(self.profile.is_factor_prompt_disabled())

    def test_factor_off(self):
        "Factor prompt should be disabled when factor is disabled. """
        self.profile.factor = 'off'
        self.assertTrue(self.profile.is_factor_prompt_disabled())

        self.profile.factor = 'OFF'
        self.assertTrue(self.profile.is_factor_prompt_disabled(),
                        "Should be case insensitive")

    def test_factor_auto(self):
        "Factor prompt should be disabled when a valid factor is given. """
        self.profile.factor = 'auto'
        self.assertTrue(self.profile.is_factor_prompt_disabled())

    def test_factor_invalid(self):
        "Factor prompt should be enabled when an invalid factor is given. """
        self.profile.factor = 'bozo'
        self.assertFalse(self.profile.is_factor_prompt_disabled())

    # Profile.is_factor_valid() tests

    def test_is_factor_auto_valid(self):
        "Auto should be a valid factor. """
        self.profile.factor = 'auto'
        self.assertTrue(self.profile.is_factor_valid())

    def test_is_factor_push_valid(self):
        "Push should be a valid factor. """
        self.profile.factor = 'push'
        self.assertTrue(self.profile.is_factor_valid())

    def test_is_factor_bozo_valid(self):
        "Bozo should not be a valid factor. """
        self.profile.factor = 'bozo'
        self.assertFalse(self.profile.is_factor_valid())

    def test_is_factor_off_valid(self):
        "Off should not be a valid factor. """
        self.profile.factor = 'off'
        self.assertFalse(self.profile.is_factor_valid())

    def test_is_factor_None_valid(self):
        "None should not be a valid factor. """
        # self.profile.factor = None
        self.assertFalse(self.profile.is_factor_valid())
