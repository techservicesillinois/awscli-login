try:
    from botocore.session import Session
except ImportError:  # pragma: no cover
    class Session():  # type: ignore
        pass

from .config import Profile, error_handler
from .util import update_credential_file, raise_if_credential_process_not_set


@error_handler()
def configure(profile: Profile, session: Session, interactive: bool = True):
    """ Interactive login profile configuration. """
    if not update_credential_file(session, profile.name):
        return

    profile.update()


@error_handler()
def exit_if_credential_process_not_set(profile: Profile, session: Session):
    """ Interactive login profile configuration. """
    session.set_credentials(None, None)  # Disable credential lookup
    raise_if_credential_process_not_set(session, profile.name)
