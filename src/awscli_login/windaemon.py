import pickle
import sys
import os
import tempfile

from daemoniker import Daemonizer


def main():
    dummy = "Hello World"
    pidFile = os.path.join("C:\\Users\\althor", "test.pid")
    testFile = os.path.join("C:\\Users\\althor", "pyTest.txt")


if __name__ == '__main__':
    dummy = "Hello World"
    argpath = sys.argv[1]
    args = None

    if os.path.exists(argpath):
        with open(argpath,'rb') as f:
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
    with Daemonizer() as (is_setup, daemonizer):
        is_parent, dummy = daemonizer(
            pidfile, dummy
        )
        if is_parent:
            print("in parent")
            dummy = "Hello Parent"
        if not is_parent:
            print("in child")
            testFile = os.path.join("C:\\Users\\althor", "pyTest.txt")
            f = open(testFile, 'a')
            f.write(dummy)
            f.close()
            if os.path.exists(os.environ["__AWS_CLI_WINDAEMON__"]):
                os.remove(os.environ["__AWS_CLI_WINDAEMON__"])
            dummy = "Hello bob"
