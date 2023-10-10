""" A collection of custom exceptions """
from .const import FACTORS


class AWSCLILogin(Exception):
    code: int = 1


class ConfigError(AWSCLILogin):
    pass


class AlreadyLoggedIn(ConfigError):
    code = 2

    def __init__(self) -> None:
        mesg = 'Already logged in!'
        super().__init__(mesg)


class AlreadyLoggedOut(ConfigError):
    code = 3

    def __init__(self) -> None:
        mesg = 'Already logged out!'
        super().__init__(mesg)


class ProfileNotFound(ConfigError):
    code = 4

    def __init__(self, profile: str) -> None:
        super().__init__(f'The login profile {profile} could not be found!\n'
                         'Configure the profile with the following command:'
                         f'\n\naws login configure --profile {profile}')


class ProfileMissingArgs(ConfigError):
    code = 5

    def __init__(self, profile: str, *args: str) -> None:
        mesg = 'The login profile (%s) is missing argument(s): %s!'
        super().__init__(mesg % (profile, ', '.join(args)))


class InvalidFactor(ConfigError):
    code = 6

    def __init__(self, factor: str) -> None:
        valid_factors = ', '.join(FACTORS) + '.'
        mesg = "Invalid factor %s! Valid values are: " + valid_factors
        super().__init__(mesg % factor)


class SAML(AWSCLILogin):
    pass


class AuthnFailed(SAML):
    code = 7

    def __init__(self) -> None:
        mesg = 'Authentication failed!'
        super().__init__(mesg)


class InvalidSOAP(SAML):
    code = 8

    def __init__(self, url: str) -> None:
        mesg = "Invalid SOAP returned by ECP Endpoint: %s!\n" % url
        mesg += "ECP Endpoint URL may be bad!"
        super().__init__(mesg)


class MissingCookieJar(SAML):
    code = 9

    def __init__(self, cookies: str) -> None:
        mesg = "Failed to load cookie jar: %s"
        super().__init__(mesg % cookies)


class RoleParseFail(SAML):
    code = 10

    def __init__(self, role: str) -> None:
        mesg = "Bad SAML Response! Failed to parse role: %s!"
        super().__init__(mesg % role)


class InvalidSelection(ConfigError):
    code = 11

    def __init__(self) -> None:
        mesg = "Invalid selection!\a"
        super().__init__(mesg)


class TooManyHttpTrafficFlags(ConfigError):
    code = 12

    def __init__(self) -> None:
        super().__init__(
            "Can not specify both --save-http-traffic"
            " and --load-http-traffic"
        )


class VcrFailedToLoad(ConfigError):
    code = 13

    def __init__(self) -> None:
        super().__init__(
            "Failed to load vcr module. "
            "Install vcr to use the --save_http_traffic\n"
            "or --load_http_traffic flags:\n\n"
            "    $ pip install vcrpy"
        )


class MissingTape(ConfigError):
    code = 14

    def __init__(self, filename) -> None:
        super().__init__(f"{filename}: No such file")


class ExistingTape(ConfigError):
    code = 15

    def __init__(self, filename) -> None:
        super().__init__(f"{filename}: file or directory already exists")


class CredentialsExpired(ConfigError):
    code = 12

    def __init__(self) -> None:
        mesg = 'Credentials Expired!'
        super().__init__(mesg)


class CredentialProcessNotSet(ConfigError):
    code = 13
    error = 'not set'

    def __init__(self, profile) -> None:
        mesg = f'Credential process is {self.error} for current profile ' \
               f'"{profile}".\nReconfigure using:\n\n' \
               'aws login configure'
        super().__init__(mesg)


class CredentialProcessMisconfigured(CredentialProcessNotSet):
    code = 14
    error = 'misconfigured'


class ConfigurationFailed(ConfigError):
    code = 15

    def __init__(self) -> None:
        mesg = 'Failed to configure profile. Finish configuration using:' \
               '\n\naws login configure'
        super().__init__(mesg)
