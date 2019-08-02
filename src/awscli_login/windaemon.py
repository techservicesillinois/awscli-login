import logging
import pickle
import sys
import os
import tempfile

from daemoniker import Daemonizer, SignalHandler1

from awscli_login.logger import configFileLogger
from awscli_login.saml import refresh
from awscli_login.util import nap


def main():
    dummy = "Hello World"
    pidFile = os.path.join("C:\\Users\\althor", "test.pid")
    testFile = os.path.join("C:\\Users\\althor", "pyTest.txt")


if __name__ == '__main__':
    dummy = "Hello World"
    argpath = sys.argv[1]
    args = None

    if os.path.exists(argpath):
        with open(argpath, 'rb') as f:
            args = pickle.load(f)
        argFile = tempfile.NamedTemporaryFile()
        tempArgPath = argFile.name + "A"
        os.environ["__AWS_CLI_WINDAEMON__"] = tempArgPath
        if not os.path.exists(os.environ["__AWS_CLI_WINDAEMON__"]):
            with open(tempArgPath, 'wb') as fw:
                # Use the highest available protocol
                pickle.dump(args, fw, protocol=-1)
        os.environ["__AWS_CLI_PID__"] = args[0].pidfile
        print("two" + args[0].pidfile)
    if os.path.exists(os.environ["__AWS_CLI_WINDAEMON__"]):
        # pass
        try:
            with open(os.environ["__AWS_CLI_WINDAEMON__"], 'rb') as f:
                args = pickle.load(f)
        except Exception as exc:
            testFile = os.path.join("C:\\Users\\althor", "pyTest.txt")
            f = open(testFile, 'a')
            f.write("error reading from " + os.environ["__AWS_CLI_WINDAEMON__"] + "{0}".format(str(exc)))
            f.close()
            raise Exception(
                'Timeout while waiting for daemon init.'
            ) from exc

        # print("one" + str(args[0].pidfile))
    pidfile = os.environ["__AWS_CLI_PID__"]
    profile = args[0]
    role = args[1]
    expires = args[2]
    with Daemonizer() as (is_setup, daemonizer):
        is_parent, profile, role, expires = daemonizer(
            pidfile, profile, role, expires
        )
        if is_parent:
            print("in parent")
            dummy = "Hello Parent"
        if not is_parent:
            sighandler = SignalHandler1(profile.pidfile)
            sighandler.start()

            logger = configFileLogger(profile.logfile, logging.INFO)
            logger.info('Starting refresh process for role %s' % role[1])

            # TODO add retries!
            while (True):
                retries = 0
