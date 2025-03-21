import os
import configparser

from botocore.exceptions import ClientError
from botocore.session import Session

from .config import error_handler
from .__main__ import save_sts_token
from .util import sort_roles
from .config import Profile
from .saml import (
    authenticate,
    refresh
)

ACCT_FILE = os.path.join(os.path.expanduser("~"), '.aws-login', 'alias')
ACCT_SECTION = "accounts"


@error_handler()
def edit_account_names(profile: Profile, session: Session):
    names = _edit_account_names(profile, session)
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
    save_sts_token(profile, sts, saml, role, profile.duration)

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
        return aliases['AccountAliases'][0]
    except ClientError:
        return None


def _edit_account_names(profile: Profile, session: Session):
    """ Print account names to STDOUT """
    session.set_credentials(None, None)  # Disable credential lookup
    sts = session.create_client('sts')
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

    account_roles = [account_id for account_id, _ in sort_roles(roles)]
    accounts = {}

    for account_id, role in list(zip(account_roles, roles)):
        if account_id not in accounts:
            if account_id in profile.account_names:
                name = profile.account_names[account_id]
            else:
                name = get_account_name(profile, session, sts, saml, role)

            value = input(f"{account_id} [{name}]: ").strip()
            if value:
                accounts[account_id] = value
            elif name is not None:
                accounts[account_id] = name

    return accounts
