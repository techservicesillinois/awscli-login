from botocore.session import Session

from .__main__ import error_handler
from .config import Profile


@error_handler()
def configure(profile: Profile, session: Session):
    """ Interactive login profile configuration. """
    profile.update()
