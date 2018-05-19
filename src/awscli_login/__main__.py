# from signal import signal, SIGINT, SIGTERM
import logging
import traceback

from argparse import Namespace
from datetime import datetime
from functools import wraps

import boto3

from botocore.session import Session
from daemoniker import Daemonizer, SignalHandler1
from daemoniker import send, SIGINT, SIGTERM, SIGABRT

from .config import (
    Profile,
    ERROR_NONE,
    ERROR_UNKNOWN,
)
from .exceptions import AlreadyLoggedOut, AWSCLILogin
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


def save_sts_token(session: Session, client, saml: str,
                   role: Role) -> datetime:
    token = client.assume_role_with_saml(
        RoleArn=role[1],
        PrincipalArn=role[0],
        SAMLAssertion=saml,
    )
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

            # TODO add retries!
            while(True):
                retries = 0
                nap(expires, 0.9)

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
                            nap(expires, 0.2)
                        else:
                            raise
                    else:
                        break

                expires = save_sts_token(session, client, saml, role)

        return is_parent


def error_handler(skip_args=True, validate=False):
    """ A decorator for exception handling and logging. """
    def decorator(f):
        @wraps(f)
        def wrapper(args: Namespace, session: Session):
            exp = None  # type: Exception
            code = ERROR_NONE
            sig = None

            try:
                configConsoleLogger(args.verbose)
                if not skip_args:
                    profile = Profile(session, args, validate)
                else:
                    profile = Profile(session, None, validate)

                f(profile, session)
            except AWSCLILogin as e:
                code = e.code
                exp = e
            except SIGINT as e:
                sig = 'SIGINT'
            except SIGABRT as e:
                sig = 'SIGABRT'
            except SIGTERM as e:
                sig = 'SIGTERM'
            except Exception as e:
                code = ERROR_UNKNOWN
                exp = e
            finally:
                if code:
                    logger.error(str(exp), exc_info=False)
                    logger.debug(traceback.format_exc())

                if sig:
                    logger.info('Received signal: %s. Shutting down...' % sig)

                exit(code)

        return wrapper
    return decorator


@error_handler(skip_args=False, validate=True)
def main(profile: Profile, session: Session):
    is_parent = True

    try:
        client = boto3.client('sts')

        # TODO force-refresh should kill refresh!
        if not profile.force_refresh:
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

        role = get_selection(roles, profile.role_arn)
        expires = save_sts_token(session, client, saml, role)

        if not profile.force_refresh:
            is_parent = daemonize(profile, session, client, role, expires)
    except Exception as e:
        raise
    finally:
        if not is_parent:
            logger.info('Exiting refresh process')


@error_handler()
def logout(profile: Profile, session: Session):
    try:
        send(profile.pidfile, SIGINT)
        remove_credentials(session)
    except IOError:
        raise AlreadyLoggedOut
