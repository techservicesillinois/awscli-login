""" A collection of custom exceptions """
from .const import FACTORS


class AWSCLILogin(Exception):
    code = 1  # type: int


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
        mesg = 'The login profile (%s) could not be found!'
        super().__init__(mesg % profile)


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
