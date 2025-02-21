import logging

from argparse import Namespace
from datetime import datetime

try:
    from botocore import client as Client
except ImportError:  # pragma: no cover
    class Client():  # type: ignore
        pass

try:
    from botocore.session import Session
except ImportError:  # pragma: no cover
    class Session():  # type: ignore
        pass


from .config import Profile, error_handler
from .exceptions import AlreadyLoggedIn, AlreadyLoggedOut
from .saml import authenticate, refresh
from ._typing import Role
from .util import (
    get_selection,
)

logger = logging.getLogger(__package__)


def save_sts_token(profile: Profile, client: Client, saml: str,
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
    profile.save_credentials(token, role)
    return token


def login(profile: Profile, session: Session, interactive: bool = True):
    session.set_credentials(None, None)  # Disable credential lookup
    client = session.create_client('sts')

    # Exit if already logged in
    if interactive:
        try:
            profile.raise_if_logged_in()
            if profile.force_refresh:
                logger.warning("Logged out: ignoring --force-refresh.")
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
    role = get_selection(roles, profile.role_arn, interactive)
    return save_sts_token(profile, client, saml, role, duration)


def logout_args(args: Namespace):
    nargs = Namespace()

    nargs.all = args.all
    del args.all

    return nargs


@error_handler(extra_args_handler=logout_args)
def logout(profile: Profile, session: Session, xargs: Namespace,
           interactive: bool = True):
    if xargs.all:
        profile.remove_all_credentials()
    else:
        if not profile.remove_credentials():
            raise AlreadyLoggedOut


@error_handler(skip_args=False, validate=True)
def main(profile: Profile, session: Session, interactive: bool = True):
    login(profile, session, interactive)
