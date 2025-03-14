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
def print_account_names(profile: Profile, session: Session):
    print(list_account_names(profile, session))


@error_handler()
def save_account_names(profile: Profile, session: Session):
    names = list_account_names(profile, session)
    write_account_names_file(names)


def write_account_names_file(account_names):
    config = configparser.ConfigParser()
    if os.path.exists(ACCT_FILE):
        config.read(ACCT_FILE)

    if not config.has_section(ACCT_SECTION):
        config.add_section(ACCT_SECTION)

    for account_id in account_names:
        if not config.has_option(ACCT_SECTION, account_id):
            config.set(ACCT_SECTION, account_id, account_names[account_id])

    with open(ACCT_FILE, 'w') as f:
        config.write(f)


def list_account_names(profile: Profile, session: Session):
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
    discovered = {}

    for account_id, role in list(zip(account_roles, roles)):
        save_sts_token(profile, sts, saml, role, profile.duration)

        params = dict(
            RoleArn=role[1],
            PrincipalArn=role[0],
            SAMLAssertion=saml,
        )
        # duration is optional and can be set by the role;
        # avoid passing if not set.

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
            default_alias = aliases['AccountAliases'][0]
            discovered[account_id] = default_alias
        except ClientError as e:
            pass  # TODO: Log something here

    return discovered
