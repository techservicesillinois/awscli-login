try:
    from botocore.session import Session
except ImportError:  # pragma: no cover
    class Session():  # type: ignore
        pass

from .config import Profile, error_handler
from .util import update_credential_file


@error_handler()
def configure(profile: Profile, session: Session, interactive: bool = True):
    """ Interactive login profile configuration. """
    if not update_credential_file(session, profile.name):
        return

    profile.update()
