from botocore.session import Session
from awscli_login.__main__ import error_handler

from awscli_login.config import (
    Profile,
)


@error_handler()
def configure(profile: Profile, session: Session):
    """ Interactive login profile configuration. """
    profile.update()
