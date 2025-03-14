# This file is a refactor of code contributed by chrisortman in PR #28
import configparser
import logging
import os

from argparse import Namespace
from typing import List, Tuple

from botocore.session import Session

from .config import error_handler, Profile
from .exceptions import AlreadyLoggedOut, AuthnFailed, PleaseLogin
from .saml import refresh
from ._typing import Role

ACCT_FILE = os.path.join(os.path.expanduser("~"), '.aws-login', 'alias')
ACCT_SECTION = "accounts"

logger = logging.getLogger(__package__)


def xargs_handler(args: Namespace):
    nargs = Namespace()

    for arg in ['auto']:
        setattr(nargs, arg, getattr(args, arg))
        delattr(args, arg)

    return nargs


@error_handler(extra_args_handler=xargs_handler)
def edit_account_names(profile: Profile, session: Session, xargs: Namespace):
    names = _edit_account_names(profile, session, xargs)
    write_account_names_file(names)


def write_account_names_file(account_names):
    config = configparser.ConfigParser()
    if os.path.exists(ACCT_FILE):
        config.read(ACCT_FILE)

    if not config.has_section(ACCT_SECTION):
        config.add_section(ACCT_SECTION)

    config[ACCT_SECTION] = account_names

    with open(ACCT_FILE, 'w') as f:
        config.write(f)


def get_account_name(profile, session, sts, saml, role):
    params = dict(
        RoleArn=role[1],
        PrincipalArn=role[0],
        SAMLAssertion=saml,
    )

    token = sts.assume_role_with_saml(**params)
    creds = token['Credentials']
    iam = session.create_client(
            'iam',
            aws_access_key_id=creds['AccessKeyId'],  # type: ignore
            aws_secret_access_key=creds['SecretAccessKey'],  # type: ignore
            aws_session_token=creds['SessionToken'],  # type: ignore
    )

    try:
        aliases = iam.list_account_aliases()
        return aliases['AccountAliases'][0].strip()
    except Exception as e:
        logger.debug(e)
        return None


def role_arns2accountid_role_arn_list(roles: List[Role]) \
        -> List[Tuple[str, Role]]:
    account_roles: List[Tuple[str, Role]] = []

    for role in roles:
        account_id: str = role[1].split(':')[4]
        account_roles.append((account_id, role))

    return account_roles


def _edit_account_names(profile: Profile, session: Session, xargs: Namespace):
    """ Print account names to STDOUT """
    session.set_credentials(None, None)  # Disable credential lookup
    sts = session.create_client('sts')

    try:
        profile.raise_if_logged_out()

        saml, roles = refresh(
            profile.ecp_endpoint_url,
            profile.cookies,
            profile.verify_ssl_certificate,
        )
    except (AlreadyLoggedOut, AuthnFailed):
        raise PleaseLogin

    account_roles = role_arns2accountid_role_arn_list(roles)
    accounts = {}
    missing = set()

    for account_id, role in account_roles:
        if account_id not in accounts:  # Don't name an account twice
            if account_id in profile.account_names:  # Prefer custom name
                name = profile.account_names[account_id]
            else:  # Lookup name on AWS if no custom name found
                name = get_account_name(profile, session, sts, saml, role)
                if not name:
                    logger.info("Unable to retrieve account name for "
                                f"account {account_id} usring role {role[1]}")
                    missing.add(account_id)
                    continue  # Skip since another role might have perms

            prompt = f"{account_id} [{name}]: "
            value = None if xargs.auto else input(prompt).strip()
            accounts[account_id] = value if value else name

    # Ask user to manually name accounts that do not return a name
    missing = missing - set(accounts)
    if not xargs.auto:
        for account_id in missing:
            value = input(f"{account_id} [None]: ").strip()
            if value:
                accounts[account_id] = value
    else:
        if missing:
            logger.warning("Unable to retrieve aliases for:\n" +
                           '\n'.join(missing))

    return accounts
