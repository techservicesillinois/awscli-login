# from signal import signal, SIGINT, SIGTERM
import logging
import os
from datetime import datetime

from botocore import client as Client
from botocore.session import Session
from daemoniker import (
    SIGINT,
    SIGTERM,
    Daemonizer,
    SignalHandler1,
    send
)

from ..exceptions import AlreadyLoggedIn, AlreadyLoggedOut
from ..logger import configFileLogger
from ..saml import authenticate, refresh
from ..typing import Role
from ..util import get_selection, nap
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


def daemonize(profile: Profile, session: Session, client: Client,
              role: Role, expires: datetime) -> bool:
    with Daemonizer() as (is_setup, daemonizer):
        is_parent, profile, session, client, role, expires = daemonizer(
            profile.pidfile,
            profile,
            session,
            client,
            role,
            expires,
        )

        if not is_parent:
            sighandler = SignalHandler1(profile.pidfile)
            sighandler.start()

            logger = configFileLogger(profile.logfile, logging.INFO)
            logger.info('Startig refresh process for role %s' % role[1])

            while True:
                try:
                    retries = 0
                    nap(expires, 0.9, profile.refresh)

                    while True:
                        try:
                            saml, _ = refresh(
                                profile.ecp_endpoint_url,
                                profile.cookies,
                            )
                        except Exception as e:
                            retries += 1

                            if (retries < 4):
                                logger.info('Refresh failed: %s' % str(e))
                                nap(expires, 0.2, profile.refresh * 0.2)
                            else:
                                raise
                        else:
                            break

                    expires = save_sts_token(session, client, saml, role)
                except SIGINT:
                    pass

        return is_parent


@error_handler(skip_args=False, validate=True)
def main(profile: Profile, session: Session):
    is_parent = True

    if profile.force_refresh:
        try:
            profile.raise_if_logged_in()
        except AlreadyLoggedIn:
            send(profile.pidfile, SIGINT)
            return

        logger.warn("Logged out: ignoring --force-refresh.")

    try:
        client = session.create_client('sts')

        # Exit if already logged in
        profile.raise_if_logged_in()

        # Must know username to lookup cookies
        profile.get_username()

        try:
            saml, roles = refresh(
                profile.ecp_endpoint_url,
                profile.cookies,
            )
        except Exception:
            creds = profile.get_credentials()
            saml, roles = authenticate(profile.ecp_endpoint_url,
                                       profile.cookies, *creds)

        duration = profile.duration
        role = get_selection(roles, profile.role_arn)
        expires = save_sts_token(session, client, saml, role, duration)

        if os.name == 'posix' and not profile.disable_refresh:
            is_parent = daemonize(profile, session, client, role, expires)
    except Exception:
        raise
    finally:
        if not is_parent:
            logger.info('Exiting refresh process')


@error_handler()
def logout(profile: Profile, session: Session):
    try:
        send(profile.pidfile, SIGTERM)
        remove_credentials(session)
    except IOError:
        raise AlreadyLoggedOut
