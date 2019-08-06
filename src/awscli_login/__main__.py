# from signal import signal, SIGINT, SIGTERM
import logging
import signal
import traceback
import sys
import os
import subprocess
import pickle


from argparse import Namespace
from datetime import datetime
from functools import wraps

import boto3

from botocore.session import Session
from daemoniker import Daemonizer, SignalHandler1
from daemoniker import send, SIGINT, SIGTERM, SIGABRT

from awscli_login.namespace_passer import _LocalNamespacePasser
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
from .awscli_typing import Role

logger = logging.getLogger(__package__)


def save_sts_token(session: Session, client, saml: str,
                   role: Role, duration) -> datetime:
    params = dict(
        RoleArn=role[1],
        PrincipalArn=role[0],
        SAMLAssertion=saml,
    )
    if duration:
        params['DurationSeconds'] = duration
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

            # TODO add retries!
            while (True):
                retries = 0
                nap(expires, 0.9)

                while (True):
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


def windowsdaemonize(profile, role, expires):
    python_path = sys.executable
    python_path = os.path.abspath(python_path)
    python_dir = os.path.dirname(python_path)
    pythonw_path = python_dir + '/pythonw.exe'
    success_timeout = 30
    with _LocalNamespacePasser() as worker_argpath:
        # Write an argvector for the worker to the namespace passer
        worker_argv = [
            profile,  # namespace_path
            role,
            expires
        ]
        with open(worker_argpath, 'wb') as f:
            # Use the highest available protocol
            pickle.dump(worker_argv, f, protocol=-1)

        # Create an env for the worker to let it know what to do
        worker_env = {}

        worker_env.update(dict(os.environ))
        # Figure out the path to the current file
        # worker_target = os.path.abspath(__file__)
        worker_cmd = f'"{python_path}" -m awscli_login.windaemon "{worker_argpath}"'
        try:
            # This will wait for the worker to finish, or cancel it at
            # the timeout.
            subprocess.run(
                worker_cmd,
                env=worker_env,
                timeout=success_timeout
            )

        except subprocess.TimeoutExpired as exc:
            raise ChildProcessError(
                'Timeout while waiting for daemon init.'
            ) from exc


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

        duration = profile.duration
        role = get_selection(roles, profile.role_arn)
        expires = save_sts_token(session, client, saml, role, duration)
        if not profile.force_refresh and not profile.disable_refresh:
            if sys.platform != 'win32':
                is_parent = daemonize(profile, session, client, role, expires)
            else:
                windowsdaemonize(profile, role, expires)

    except Exception as e:
        raise
    finally:
        if not is_parent:
            logger.info('Exiting refresh process')


@error_handler()
def logout(profile: Profile, session: Session):
    try:
        send(profile.pidfile, SIGINT)
        if os.path.exists(profile.pidfile):
            os.remove(profile.pidfile)
        remove_credentials(session)
    except IOError:
        raise AlreadyLoggedOut
