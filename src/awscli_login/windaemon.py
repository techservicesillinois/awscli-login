import datetime
import pickle
import sys
import os

from awscli_login.typing import Role

from awscli_login.config import Profile
from daemoniker import Daemonizer


def main():
    dummy = "Hello World"
    pidFile = os.path.join("C:\\Users\\althor.FC-OME-JEFFERSO", "test.pid")
    testFile = os.path.join("C:\\Users\\althor.FC-OME-JEFFERSO", "pyTest.txt")
    with Daemonizer() as (is_setup, daemonizer):
        if is_setup:
            pass
        is_parent, dummy = daemonizer(
            pidFile, dummy
        )
        if is_parent:
            print("in parent")
            dummy = "Hello Parent"
        if not is_parent:
            print("in child")
            dummy = "Hello bob"
            f = open(testFile, 'w')
            f.write("Hello")
            f.close()


if __name__ == '__main__':
    print("hello")

    argpath = os.environ.get("__AWSCLI_LOGIN_DAEMON_PATH__")
    del os.environ['__AWSCLI_LOGIN_DAEMON_PATH__']
    with open(argpath, 'rb') as f:
        args = pickle.load(f, fix_imports=True)
    print(str(args))
    main()
    print("done")
    sys.exit(2)
