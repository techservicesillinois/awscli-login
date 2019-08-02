import sys
import os

from daemoniker import Daemonizer


def main():
    dummy = "Hello World"
    pidFile = os.path.join("C:\\Users\\althor", "test.pid")
    testFile = os.path.join("C:\\Users\\althor", "pyTest.txt")


if __name__ == '__main__':
    dummy = "Hello World"
    with Daemonizer() as (is_setup, daemonizer):
        is_parent, dummy = daemonizer(
            os.path.join("C:\\Users\\althor", "test.pid"), dummy
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
            dummy = "Hello bob"
