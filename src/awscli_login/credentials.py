"""Returns AWS STS credentials"""

import argparse
import json

from datetime import datetime

from botocore.session import Session

from .__main__ import login
from .config import Profile, error_handler


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
        type=str,
        help="AWS profile name")
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Display verbose information")
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
    _main(args, session)


if __name__ == "__main__":
    main()
