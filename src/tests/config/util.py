""" Utility functions """
import contextlib

from os import remove
from typing import Any, Dict, List, Optional  # NOQA

from awscli_login.config import Profile


class MockSession:
    """
    Minimal mock session class needed for class Profile init.
    """
    profile = None  # type: Optional[str]

    def __init__(self, profile: str = None) -> None:
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
    r = []  # type: List[str]

    for key in profile._config_options.keys():
        r.append(str(expected_attr_vals.get(key, '')))
    return r
