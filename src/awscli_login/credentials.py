"""Returns AWS STS credentials"""

import argparse
import json
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
        "-V",
        "--version-info",
        action="count",
        default=0,
        help="Display version information")

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


def main():
    # https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sourcing-external.html
    args = init_parser().parse_args()
    session = Session(profile=args.profile)
    if args.version_info:
        print(f"{version}\t{sys.executable}\t{sys.version}\t{sys.path}")
    elif args.login:
        ns = Namespace(**json.load(args.login))
        if ns.version_info:  # TODO: implement in login?
            print(f"{version}\t{sys.executable}\t{sys.version}\t{sys.path}")
            return
        return login(ns, session)
    elif args.logout:
        return logout(Namespace(**json.load(args.logout)), session)
    else:
        return _main(args, session)


if __name__ == "__main__":
    main()
