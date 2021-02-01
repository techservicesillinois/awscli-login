# from signal import signal, SIGINT, SIGTERM
import sys
import logging
import traceback
import os

from argparse import Namespace
from datetime import datetime
from functools import wraps
from typing import Optional

import boto3

from botocore.session import Session
from daemoniker import Daemonizer, SignalHandler1
from daemoniker import send, SIGINT, SIGTERM, SIGABRT

from .config import (
    Profile,
    ERROR_NONE,
    ERROR_UNKNOWN,
)
from .exceptions import (
    AWSCLILogin,
    AlreadyLoggedIn,
    AlreadyLoggedOut,
)
from .logger import (
    configConsoleLogger,
    configFileLogger,
)
from .saml import (
    authenticate,
    refresh,
)
from .util import (
    get_selection,
    nap,
    remove_credentials,
    save_credentials,
)
from .typing import Role

logger = logging.getLogger(__package__)


def save_sts_token(session: Session, client: boto3.client, saml: str,
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


def daemonize(profile: Profile, session: Session, client: boto3.client,
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

            while(True):
                try:
                    retries = 0
                    nap(expires, 0.9, profile.refresh)

                    while(True):
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


def error_handler(skip_args=True, validate=False):
    """ A decorator for exception handling and logging. """
    def decorator(f):
        @wraps(f)
        def wrapper(args: Namespace, session: Session):
            exp = None  # type: Optional[Exception]
            exc_info = None
            code = ERROR_NONE
            sig = None

            try:
                # verbosity can only be set at command line
                configConsoleLogger(args.verbose)
                del args.verbose

                if not skip_args:
                    profile = Profile(session, args, validate)
                else:
                    profile = Profile(session, None, validate)

                f(profile, session)
            except AWSCLILogin as e:
                exc_info = sys.exc_info()
                code = e.code
                exp = e
            except SIGINT:
                sig = 'SIGINT'
            except SIGABRT:
                sig = 'SIGABRT'
            except SIGTERM:
                sig = 'SIGTERM'
            except Exception as e:
                exc_info = sys.exc_info()
                code = ERROR_UNKNOWN
                exp = e
            finally:
                if exp:
                    logger.error(str(exp), exc_info=False)

                if exc_info:
                    logger.debug(
                        '\n' + ''.join(traceback.format_exception(*exc_info))
                    )

                if sig:
                    logger.info('Received signal: %s. Shutting down...' % sig)

                exit(code)

        return wrapper
    return decorator


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
        client = boto3.client('sts')

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
