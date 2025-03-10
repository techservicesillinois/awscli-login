"""Returns AWS STS credentials"""

import argparse
import json
import os
import platform
import sys

from argparse import Namespace
from datetime import datetime

from botocore.session import Session

from .__main__ import main as login, logout
from .config import Profile, error_handler
from ._version import version


def print_credentials(token):
    if token is not None:
        creds = token['Credentials']
        creds['Version'] = 1
        creds['Expiration'] = creds['Expiration'].isoformat()
    else:
        creds = {
            "Version": 1,
            "AccessKeyId": "",
            "SecretAccessKey": "",
            "SessionToken": "",
            "Expiration": datetime(1970, 1, 1),
        }
    print(json.dumps(creds))


def init_parser():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-p",
        "--profile",
        default=None,
        type=str,
        help="AWS profile name")
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Display verbose information")
    parser.add_argument(
        "-d",
        "--debug-info",
        action='store_true',
        help="Display debug information")

    hidden = parser.add_mutually_exclusive_group()
    for flag in ["--login", "--logout"]:
        hidden.add_argument(flag, type=argparse.FileType('r'),
                            help=argparse.SUPPRESS)
    return parser


@error_handler()
def _main(profile: Profile, session: Session, interactive: bool = True):
    profile.raise_if_logged_out()
    if profile.are_credentials_expired():
        token = login(profile, session, interactive=False)
    else:
        token = profile.load_credentials()
    print_credentials(token)


def debug_info():
    executable = sys.executable if platform.system() != "Windows" else \
        sys.executable.lower()
    nl = "\n"  # Workaround for versions before 3.12 (See PEP 701)
    info = f"Version: {version}\n" f"Python executable: {executable}\n" \
           f"Python Version: {platform.python_version()}\n" \
           f"Python Compiler: {platform.python_compiler()}\n" \
           f"Python Implementation: {sys.implementation}\n" \
           f"Python Path:\n{nl.join(sys.path)}\n" \
           f"System Path:\n{nl.join(sys.path)}\n"

    def env(func):
        ignore = [
            "AWS_DATA_PATH",
            "SHLVL",
            "_",
            "_PYI_ARCHIVE_FILE",
            "_PYI_PARENT_PROCESS_LEVEL",
        ]

        return "Environment:\n" + '\n'.join(sorted([
            f"{k}: {func(v)}" for k, v in os.environ.items()
            if k not in ignore
        ]))

    if platform.system() == 'Windows':
        environment = env(lambda x: x.lower().strip())
    else:
        environment = env(lambda x: x)
    print(info + environment)


def main():
    # https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sourcing-external.html
    args = init_parser().parse_args()
    session = Session(profile=args.profile)
    if args.debug_info:
        debug_info()
    elif args.login:
        ns = Namespace(**json.load(args.login))
        if ns.debug_info:
            debug_info()
            return
        return login(ns, session)
    elif args.logout:
        return logout(Namespace(**json.load(args.logout)), session)
    else:
        return _main(args, session)


if __name__ == "__main__":
    main()
