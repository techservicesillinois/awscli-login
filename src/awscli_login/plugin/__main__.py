import logging
from datetime import datetime

from botocore import client as Client
from botocore.session import Session

from ..exceptions import AlreadyLoggedIn
from ..saml import authenticate, refresh
from .._typing import Role
from ..util import get_selection
from .config import Profile
from .util import error_handler, remove_credentials, save_credentials

logger = logging.getLogger(__package__)


def save_sts_token(session: Session, client: Client, saml: str,
                   role: Role, duration: int = 0) -> datetime:
    params = dict(
        RoleArn=role[1],
        PrincipalArn=role[0],
        SAMLAssertion=saml,
    )
    if duration:
        # Mypy reports that DurationSeconds should be a string but
        # botocore dies unless it is an int so ignore mypy.
        params['DurationSeconds'] = duration  # type: ignore[assignment]
        # duration is optional and can be set by the role;
        # avoid passing if not set.

    token = client.assume_role_with_saml(**params)
    logger.info("Retrieved temporary Amazon credentials for role: " + role[1])

    return save_credentials(session, token)


def login(profile: Profile, session: Session, interactive: bool = True):
    session.set_credentials(None, None)  # Disable credential lookup
    client = session.create_client('sts')

    try:
        profile.raise_if_logged_in()
        if profile.force_refresh:
            logger.warn("Logged out: ignoring --force-refresh.")
    except AlreadyLoggedIn:
        if not profile.force_refresh:
            raise

    # Must know username to lookup cookies
    profile.get_username()

    try:
        saml, roles = refresh(
            profile.ecp_endpoint_url,
            profile.cookies,
            profile.verify_ssl_certificate,
        )
    except Exception:
        if interactive:
            creds = profile.get_credentials()
            saml, roles = authenticate(profile.ecp_endpoint_url,
                                       profile.cookies, *creds,
                                       profile.verify_ssl_certificate)
        else:
            raise

    duration = profile.duration
    role = get_selection(roles, profile.role_arn)
    return save_sts_token(session, client, saml, role, duration)


@error_handler()
def logout(profile: Profile, session: Session):
    remove_credentials(session)


@error_handler(skip_args=False, validate=True)
def main(profile: Profile, session: Session, interactive: bool = True):
    login(profile, session, interactive)
