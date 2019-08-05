import logging
import pickle
import sys
import os
import tempfile

from daemoniker import Daemonizer, SignalHandler1

from awscli_login.logger import configFileLogger
from awscli_login.saml import refresh
from awscli_login.util import nap


def main():
    args = lookup_args()
    daemonize_for_windows(*args)


def lookup_args():
    args = None
    argpath = sys.argv[1]
    if os.path.exists(argpath):
        args = load_args_for_parent(argpath, args)
        return args
    elif os.path.exists(os.environ["__AWS_CLI_WINDAEMON__"]):
        try:
            args = load_args_for_child(args)
            return args
        except Exception as exc:
            raise Exception(
                'Problem loading args from file'
            ) from exc


def load_args_for_child(args):
    with open(os.environ["__AWS_CLI_WINDAEMON__"], 'rb') as f:
        args = pickle.load(f)
    cleanup_tmp_file()
    return args


def load_args_for_parent(argpath, args):
    with open(argpath, 'rb') as f:
        args = pickle.load(f)
    store_args_for_child(args)
    return args


def store_args_for_child(args):
    argFile = tempfile.NamedTemporaryFile()
    tempArgPath = argFile.name + "A"
    os.environ["__AWS_CLI_WINDAEMON__"] = tempArgPath

    if not os.path.exists(os.environ["__AWS_CLI_WINDAEMON__"]):
        with open(tempArgPath, 'wb') as fw:
            # Use the highest available protocol
            pickle.dump(args, fw, protocol=-1)


def cleanup_tmp_file():
    with open(os.environ["__AWS_CLI_WINDAEMON__"], 'r+b') as f:
        to_erase = f.read()
        eraser = bytes(len(to_erase))
        f.seek(0)
        f.write(eraser)
    os.remove(os.environ["__AWS_CLI_WINDAEMON__"])
    del os.environ["__AWS_CLI_WINDAEMON__"]


def daemonize_for_windows(profile, role, expires):
    pidfile = profile.pidfile
    with Daemonizer() as (is_setup, daemonizer):
        is_parent, profile, role, expires = daemonizer(
            pidfile, profile, role, expires
        )
        if not is_parent:
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

                profile_name = profile.name if profile.name else 'default'
                session = boto3.Session(profile=profile_name)
                client = boto3.client('sts')
                expires = save_sts_token(session, client, saml, role)


if __name__ == '__main__':
    main()
