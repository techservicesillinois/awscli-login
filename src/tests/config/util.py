""" Utility functions """
import contextlib

from os import remove
from typing import Any, Dict, List, Optional

from awscli_login.config import Profile
from awscli_login.util import token


class MockSession:
    """
    Minimal mock session class needed for class Profile init.
    """
    profile: Optional[str] = None

    def __init__(self, profile: Optional[str] = None) -> None:
        self.profile = profile


def qremove(filename: str):
    """
    Removes a file quietly i.e. no error thrown if the file does
    not exist.
    """
    with contextlib.suppress(FileNotFoundError):
        remove(filename)


def user_input(profile: Profile,
               expected_attr_vals: Dict[str, Any]) -> List[str]:
    """ Returns values that profile.update() modifies """
    r: List[str] = []

    for key in profile._config_options.keys():
        r.append(str(expected_attr_vals.get(key, '')))
    return r


def test_token(akey: str, skey: str, stoken: str) -> Dict[str, Dict[str, Any]]:
    return token(akey, skey, stoken, "2021-02-11T00:42:09Z")
