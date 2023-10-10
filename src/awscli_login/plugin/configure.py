from botocore.session import Session

from .util import error_handler
from .config import Profile
from .util import update_credential_file


@error_handler()
def configure(profile: Profile, session: Session, interactive: bool = True):
    """ Interactive login profile configuration. """
    update_credential_file(session, profile.name)
    profile.update()
