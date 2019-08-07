from botocore.session import Session
import boto3
from .__main__ import error_handler, save_sts_token
from .util import sort_roles
from .config import Profile
from .saml import (
    authenticate,
    refresh
)
import os
import configparser

accountsfile = os.path.join(
                         os.path.expanduser("~"),
                         '.aws-login',
                         'accounts.ini'
                        )


@error_handler()
def print_account_names(profile: Profile, session: Session):
    print(list_account_names(profile,session))


@error_handler()
def save_account_names(profile: Profile, session: Session):
    names = list_account_names(profile, session)
    write_account_names_file(names)


def write_account_names_file(account_names):
    config = configparser.ConfigParser()
    if os.path.exists(accountsfile):
        config.read(accountsfile)

    if not config.has_section("ACCOUNT_NAMES"):
        config.add_section("ACCOUNT_NAMES")

    for account_id in account_names:
        if not config.has_option("ACCOUNT_NAMES", account_id):
            config.set("ACCOUNT_NAMES",account_id, account_names[account_id])

    with open(accountsfile,'w') as f:
        config.write(f)

def list_account_names(profile: Profile, session: Session):
    """ Print account names to STDOUT """
    
    sts = boto3.client('sts')

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

    for account_id, role  in list(zip(account_roles,roles)):
        save_sts_token(session, sts, saml, role, profile.duration)

        params = dict(
            RoleArn=role[1],
            PrincipalArn=role[0],
            SAMLAssertion=saml,
        )
        # duration is optional and can be set by the role;
        # avoid passing if not set.

        token = sts.assume_role_with_saml(**params)
        creds = token['Credentials']
        iam = boto3.client(
                'iam',
                aws_access_key_id=creds['AccessKeyId'],
                aws_secret_access_key=creds['SecretAccessKey'],
                aws_session_token=creds['SessionToken']
        )

        aliases = iam.list_account_aliases()
        default_alias = aliases['AccountAliases'][0]
        discovered[account_id] = default_alias

    return discovered
