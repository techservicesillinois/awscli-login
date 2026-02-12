import logging
import unittest

from argparse import Namespace
from unittest.mock import patch

from awscli_login.config import error_handler

from .login import MockBotocoreClient

BOTO_ERR = "ERROR:awscli_login.config:'MockBotocoreClient' " \
           "object has no attribute 'profile'"

root = logging.getLogger()


class ErrorHandler(unittest.TestCase):

    @patch("awscli_login.config.Profile")
    def _test_error_handler(self, args, mesg, patch):
        @error_handler()
        def func(profile, session):
            raise Exception(mesg)

        func(args, MockBotocoreClient())

    def _test_log_level(self, verbose: int, level):
        self._test_error_handler(Namespace(verbose=verbose), "I am the law!")
        self.assertEqual(root.level, level)

    def test_error_handler_logs_exception(self):
        """ Ensure error_handler logs exception. """
        mesg = "First and only exception."
        with self.assertLogs() as cm:
            self._test_error_handler(Namespace(verbose=0), mesg)

        self.assertEqual(cm.output, [
            f"ERROR:awscli_login.config:{mesg}",
        ])

    def test_error_handler_logging_level_warn(self):
        """ error_nandler sets log level to WARN w/o verbose flag. """
        self._test_log_level(0, logging.WARN)

    # Regression test #260
    def test_error_handler_logging_level_info(self):
        """ error_nandler sets log level to INFO w/one verbose flag. """
        self._test_log_level(1, logging.INFO)

    # Regression test #260
    def test_error_handler_logging_level_debug(self):
        """ error_nandler sets log level to DEBUG w/two verbose flag. """
        self._test_log_level(2, logging.DEBUG)

    # Regression test #260
    def test_error_handler_logging_level_notset(self):
        """ error_nandler sets log level to NOTSET w/three verbose flag. """
        self._test_log_level(3, logging.NOTSET)
