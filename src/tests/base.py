import os
import stat
import sys
import unittest

from os import environ, makedirs, path, walk, unlink
from os.path import dirname, relpath, join
from tempfile import TemporaryDirectory
from typing import Any, Callable, List, Optional  # NOQA
from unittest.mock import patch

from awscli_login.config import CONFIG_FILE

from .util import exec_awscli, fork, isFileChangedBy, isFileTouchedBy, tree
from .exceptions import NotRelativePathError

PERMISSIONS = [
    ('r', 'read'),
    ('w', 'write'),
    ('x', 'execute')
]

FLAGS = {
    'Owner': {
        'r': stat.S_IRUSR,
        'w': stat.S_IWUSR,
        'x': stat.S_IXUSR,
    },
    'Group': {
        'r': stat.S_IRGRP,
        'w': stat.S_IWGRP,
        'x': stat.S_IXGRP,
    },
    'Others': {
        'r': stat.S_IRGRP,
        'w': stat.S_IWGRP,
        'x': stat.S_IWGRP,
    },
}


class SDGTestCase(unittest.TestCase):
    """Adds additional convenience assert statements.

    .. testsetup::

        from tests.base import SDGTestCase
        self = SDGTestCase
    """
    maxDiff = None

    @staticmethod
    def assertHasFilePerms(path: str, owner: str = '', group: str = '',
                           others: str = '') -> None:
        info = os.stat(path)

        users = [
            ('Owner', owner),
            ('Group', group),
            ('Others', others),
        ]

        for user, perms in users:
            for p, perm in PERMISSIONS:
                hasPerm = bool(info.st_mode & FLAGS[user][p])

                if p in perms and not hasPerm:
                    raise AssertionError(
                        '%s does not have %s permission!' % (user, perm)
                    )
                elif p not in perms and hasPerm:
                    raise AssertionError(
                        '%s has %s permission!' % (user, perm)
                    )

    @staticmethod
    def _assertHasAttr(obj: object, attr: str, evalue: Any) -> Optional[str]:
        """Assert object has an attribute with a given value.

        Example:
            This is an example.

        Args:
            obj: object to test.
            attr: attribute name.
            evalue: expected value.

        Returns:
            Error message or None.
        """
        objName = obj.__class__.__name__

        try:
            rvalue = getattr(obj, attr)
        except AttributeError:
            return "%s object does not have attr: %s" % (objName, attr)

        if type(rvalue) != type(evalue):
            return "Attribute %s has unexpected type: %s\n" \
                   "Expected %s on %s object!" % \
                   (attr, type(rvalue), type(evalue), object)

        if rvalue != evalue:
            return "Attribute %s has unexpected value: %s\n" \
                   "Expected %s on %s object!" % \
                   (attr, rvalue, evalue, objName)

        return None

    @staticmethod
    def assertHasAttr(obj: object, attr: str, evalue: Any) -> None:
        """Assert object has an attribute with a given value.

        Args:
            obj: object to test.
            attr: attribute name.
            evalue: expected value.

        Raises:
            AssertionError

        Examples:
            Consider the following simple class:

            >>> class Coordinates:
            ...     x = 0
            ...     y = 0
            ...
            >>> center = Coordinates()

            A simple passing test is the following:

            >>> self.assertHasAttr(center, 'x', 0)

            The following are various failing tests and the error's
            they raise:

            >>> self.assertHasAttr(center, 'foo', 'bar')
            Traceback (most recent call last):
                ...
            AssertionError: Coordinates object does not have attr: foo

            >>> self.assertHasAttr(center, 'x', 'bar')
            Traceback (most recent call last):
                ...
            AssertionError: Attribute x has unexpected type <class 'int'>
            Expected <class 'str'> on Coordinates object!

            >>> self.assertHasAttr(center, 'x', 1)
            Traceback (most recent call last):
                ...
            AssertionError: Attribute x has unexpected value 0
            Expected 1 on Coordinates object!
        """
        error = SDGTestCase._assertHasAttr(obj, attr, evalue)

        if error:
            raise AssertionError(error)

    @staticmethod
    def assertHasAttrs(obj: object, **kwargs: Any) -> None:
        """Assert object has attributes with given values.

        Tests if object `obj` has all the given named arguments as
        attributes with the corresponding named argument values.

        Args:
            obj: object to test.
            **kwargs: each keyword argument's name is expected to
                be an attribute on object `obj` having the same value
                as the keyword argument.

        Raises:
            AssertionError

        Examples:
            Consider the following simple class:

            >>> class Coordinates:
            ...     x = 0
            ...     y = 0
            ...
            >>> center = Coordinates()

            A simple passing test is the following:

            >>> self.assertHasAttrs(center, x=0, y=0)

            The following are various failing tests and the error's
            they raise:

            >>> self.assertHasAttrs(center, foo='bar', x=0, y=0)
            Traceback (most recent call last):
                ...
            AssertionError: Coordinates object does not have attr: foo

            >>> self.assertHasAttrs(center, x='bar', y='foo')
            Traceback (most recent call last):
                ...
            AssertionError: Attribute x has unexpected type <class 'int'>
            Expected <class 'str'> on Coordinates object!

            >>> self.assertHasAttrs(center, x=1, y=0)
            Traceback (most recent call last):
                ...
            AssertionError: Attribute x has unexpected value 0
            Expected 1 on Coordinates object!
        """
        errors = []  # type: List[str]

        for attr, value in kwargs.items():
            error = SDGTestCase._assertHasAttr(obj, attr, value)

            if error:
                errors.append(error)

        if len(errors):
            raise AssertionError('\n'.join(errors))


class TempDir(SDGTestCase):
    """A class for tests that require a temporary directory.

    This class creates a temporary directory during the setUp phase
    before each test is run. The temporary directory is destroyed
    after the test finishes even if the test failes.

    Attributes:
        tmpd (:obj:`tempfile.TemporaryDirectory`): The `TemporaryDirectory`
            object created.
    """

    def setUp(self) -> None:
        """Creates an empty temporary directory. """
        self.tmpd = TemporaryDirectory()
        self.addCleanup(self.tmpd.cleanup)

    def _abspath(self, rel_file_path) -> str:
        """Returns an absolute path rooted in a temporary directory.

        Args:
            rel_file_path: A relative file path.

        Returns:
            The absolute path to `tmpd/rel_file_path`.

        Raises:
            NotRelativePathError: If `rel_file_path` is an absolute path.
        """
        if path.isabs(rel_file_path):
            raise NotRelativePathError(rel_file_path)
        return join(self.tmpd.name, rel_file_path)

    def read(self, rel_file_path: str) -> str:
        """Reads a temporary file.

        Args:
            rel_file_path: A relative file path.

        Returns:
            The contents of file `rel_file_path` rooted in temporary
            directory `tmpd.name`.

        Raises:
            NotRelativePathError: If `rel_file_path` is an absolute path.
            FileNotFoundError: If `rel_file_path` does not exist.
        """
        filename = self._abspath(rel_file_path)

        with open(filename, 'r') as f:
            value = f.read()

        return value

    def write(self, rel_file_path: str, value) -> None:
        """Writes a given value to a temporary file.

        The file is rooted in a temporary directory using the given
        relative path `rel_file_path`. If `value` is None the file
        will be removed from disk, otherwise the value is written
        to disk.

        Args:
            rel_file_path: A relative file path.
            value: String to write to disk.

        Raises:
            NotRelativePathError: If `rel_file_path` is an absolute path.
        """
        filename = self._abspath(rel_file_path)

        if value is not None:
            with open(filename, 'w') as f:
                f.write(value)
        else:
            try:
                unlink(filename)
            except FileNotFoundError:
                pass

    def dump(self):
        """Dumps temporary directory contents into an exception.

        Raises an exception containing a listing of the temporary directory
        contents, followed by the file contents, and the current enviroment.
        Useful for debugging.

        Raises:
            AssertionError
        """
        errors = '\n---------- Temporary Directory Listing ---------\n'
        errors += tree(self.tmpd.name)
        errors += '\n------------ File Contents --------------------\n'

        for (dirpath, dirnames, filenames) in walk(self.tmpd.name):
            path = relpath(dirpath, self.tmpd.name)

            for fn in filenames:
                errors += join(path, fn) + ':\n'
                with open(join(dirpath, fn), 'r') as f:
                    errors += f.read() + '\n---\n'

        errors += '-------------- Enviroment -----------------------\n'

        errors += '--- Enviroment ---\n'
        for key, value in environ.items():
            errors += "%s=%s\n" % (key, value)

        errors += '\n-----------------------------------------------\n'
        raise AssertionError(errors)

    def assertTmpFileChangedBy(self, filename: str, func: Callable,
                               *args, **kwargs) -> None:
        """Asserts file is changed by a function.

        Args:
            filename: The file to test.
            func: The function to call.
            *args: positional arguments to pass to `func`.
            **kwargs: keyword arguments to pass to `func`.

        Raises:
            AssertionError if file is not changed.
        """
        if not isFileChangedBy(filename, func, *args, **kwargs):
            raise AssertionError('File was not changed: %s' %
                                 relpath(filename, self.tmpd.name))

    def assertTmpFileNotChangedBy(self, filename: str, func: Callable,
                                  *args, **kwargs) -> None:
        """Asserts file is not changed by a function.

        Args:
            filename: The file to test.
            func: The function to call.
            *args: positional arguments to pass to `func`.
            **kwargs: keyword arguments to pass to `func`.

        Raises:
            AssertionError if file is changed.
        """
        if isFileChangedBy(filename, func, *args, **kwargs):
            raise AssertionError('File was changed: %s' %
                                 relpath(filename, self.tmpd.name))

    def assertTmpFileTouchedBy(self, filename: str, func: Callable,
                               *args, **kwargs) -> None:
        """Asserts file is touched by a function.

        Args:
            filename: The file to test.
            func: The function to call.
            *args: positional arguments to pass to `func`.
            **kwargs: keyword arguments to pass to `func`.

        Raises:
            AssertionError if file is not touched.
        """
        if not isFileTouchedBy(filename, func, *args, **kwargs):
            raise AssertionError('File was not touched: %s' %
                                 relpath(filename, self.tmpd.name))

    def assertTmpFileNotTouchedBy(self, filename: str, func: Callable,
                                  *args, **kwargs) -> None:
        """Asserts file is not touched by a function.

        Args:
            filename: The file to test.
            func: The function to call.
            *args: positional arguments to pass to `func`.
            **kwargs: keyword arguments to pass to `func`.

        Raises:
            AssertionError if file is touched.
        """
        if isFileTouchedBy(filename, func, *args, **kwargs):
            raise AssertionError('File was touched: %s' %
                                 relpath(filename, self.tmpd.name))


class CleanAWSLoginEnvironment(TempDir):
    """Sets up a clean environment for testing aws-login Profiles.

    This works by creating a temporary directory and setting it up
    as the home directory to be used by `awscli_login.config.Profile`.
    """

    @property
    def login_config(self) -> str:
        """Contents of `tmpd/.aws-login/config`. """
        return self.read(CONFIG_FILE)

    @login_config.setter
    def login_config(self, value: str) -> None:
        self.write(CONFIG_FILE, value)

    @property
    def login_config_path(self) -> str:
        """Full path to `tmpd/.aws-login/config`. """
        return self._abspath(CONFIG_FILE)

    def setUp(self) -> None:
        """Creates `tmpd/.aws-login/config` and patches `awscli_login.config` to
        use it. """
        super().setUp()
        makedirs(dirname(self.login_config_path), 0o700)

        patcher = patch(
                'awscli_login.config.expanduser',
                return_value=self.tmpd.name
        )
        self.home = patcher.start()
        self.addCleanup(patcher.stop)


class CleanAWSEnvironment(TempDir):
    """Class for testing the AWS CLI.

    Sets up a clean test environment for working with the AWS CLI
    in a temporary directory.
    """

    @property
    def profile(self) -> Optional[str]:
        """Contents of environment variable AWS_PROFILE. """
        return environ.get('AWS_PROFILE')

    @profile.setter
    def profile(self, value: str) -> None:
        self._set_environ('AWS_PROFILE', value)

    AWS_CONFIG_FILE = '.aws/config'

    @property
    def aws_config(self) -> str:
        """Contents of the AWS config file. """
        return self.read(CleanAWSEnvironment.AWS_CONFIG_FILE)

    @aws_config.setter
    def aws_config(self, value: str) -> None:
        self.write(CleanAWSEnvironment.AWS_CONFIG_FILE, value)

    @property
    def aws_config_path(self) -> str:
        """Full path to AWS config file. """
        return self._abspath(self.AWS_CONFIG_FILE)

    AWS_CREDENTIALS_FILE = '.aws/credentials'

    @property
    def aws_credentials(self) -> str:
        """Contents of the AWS shared credentials file. """
        return self.read(CleanAWSEnvironment.AWS_CREDENTIALS_FILE)

    @aws_credentials.setter
    def aws_credentials(self, value: str) -> None:
        self.write(CleanAWSEnvironment.AWS_CREDENTIALS_FILE, value)

    @property
    def aws_credentials_path(self) -> str:
        """Full path to the AWS shared credentials file. """
        return self._abspath(self.AWS_CREDENTIALS_FILE)

    def assertAwsCredentialsEquals(self, credentials: str) -> None:
        """Assert AWS shared credentials file equals given value.

        Args:
            credentials: Value to compare AWS shared credentials file to.

        Raises:
            AssertionError
        """
        aws_credentials = self.aws_credentials
        self.assertEqual(
            aws_credentials,
            credentials,
            'Did not expect:\n' + aws_credentials + '---',
        )

    def _set_environ(self, key: str, value) -> None:
        """Set key in environment to value.

        Note:
            If value is None the key is removed from the
            environment.
        """
        if value is not None:
            environ[key] = value
        else:
            environ.pop(key, None)

    def _clear_environ(self, name: str) -> None:
        """Removes an environment variable from the environment.

        Ensures that after the test has finished the environment
        is restored, even if the test failes with an exception.
        """
        try:
            value = environ.pop(name)
        except KeyError:
            self.addCleanup(environ.pop, name, None)
        else:
            self.addCleanup(environ.update, {name: value})

    def setUp(self) -> None:
        """Creates an empty AWS environment in a temporary directory.

        Clears all AWS environment variables, and sets AWS_CONFIG_FILE
        and AWS_SHARED_CREDENTIALS_FILE to the empty temporary
        directory `tmpd/.aws`.

        Note:
            All cleared environment variables are restored after tearDown.
        """
        super().setUp()
        makedirs(dirname(self.aws_config_path), 0o700)

        # Clear all Amazon environment variables
        # https://docs.aws.amazon.com/cli/latest/topic/config-vars.html

        # General Options
        self._clear_environ('AWS_CONFIG_FILE')
        self._clear_environ('AWS_PROFILE')
        self._clear_environ('AWS_DEFAULT_REGION')
        self._clear_environ('AWS_DEFAULT_OUTPUT')
        self._clear_environ('AWS_CA_BUNDLE')

        # Credentials
        self._clear_environ('AWS_SHARED_CREDENTIALS_FILE')
        self._clear_environ('AWS_ACCESS_KEY_ID')
        self._clear_environ('AWS_SECRET_ACCESS_KEY')
        self._clear_environ('AWS_SESSION_TOKEN')
        self._clear_environ('AWS_METADATA_SERVICE_TIMEOUT')
        self._clear_environ('AWS_METADATA_SERVICE_NUM_ATTEMPTS')

        # Tell the awscli to use tmpd instead of $HOME
        self._set_environ('AWS_CONFIG_FILE', self.aws_config_path)
        self._set_environ('AWS_SHARED_CREDENTIALS_FILE',
                          self.aws_credentials_path)


class CleanTestEnvironment(CleanAWSLoginEnvironment, CleanAWSEnvironment):
    """Sets up a clean test environment in a temporary directory. """


# These tests depend on wurlitzer. wurlitzer does NOT support Windows:
# https://github.com/minrk/wurlitzer/issues/12
@unittest.skipIf(sys.platform.startswith("win"), "Windows is NOT supported!")
class IntegrationTests(CleanTestEnvironment):

    def setUp(self):
        """Configures plugin to work with the awscli. """
        super().setUp()

        # TODO Should this be split out? TODO THIS SHOULD BE A TEST!
        # exec_awscli('configure', 'set', 'plugins.login', 'awscli_login')
        self.aws_config = '[plugins]\nlogin = awscli_login\n'

    def assertAwsCliReturns(self, *args, stdout='',
                            stderr='', code=0, calls=None):
        """Runs awscli and tests the output.

        This test runs the awscli command with `*args`. It tests
        that the exit code and stdout and stderr match the given
        expect values.

        Example:
            `self.assertAwsCliReturns('logout')` is equivalent to running:

                $ aws logout

            The test in this example will pass if `aws logout` returns
            exit code 0 and emits no output to stdout or stderr.
            Otherwise an AssertionError is raised.

        Args:
            *args (str): Arguments to be passed to the AWS command
                line utility.
            stdout (str): Expected output to stdout.
            stderr (str): Expected output to stderr.
            code (int): Expected return code.
            calls (list(unittest.mock.call)): List of expected calls.

        Raises:
            AssertionError
        """
        t_out, t_err, t_code, cmd = _assertAwsCliReturns(args, calls)

        mesg = "Error: ran '%s', on %s expected output: %s"
        self.assertEqual(
            t_out,
            stdout,
            mesg % (cmd, 'stdout', stdout)
        )
        self.assertEqual(
            t_err,
            stderr,
            mesg % (cmd, 'stderr', stderr)
        )
        self.assertEqual(
            t_code,
            code,
            "Error: '%s' returned %d, expected: %d" %
            (cmd, t_code, code)
        )


@fork()
def _assertAwsCliReturns(args, calls):
    t_code = None

    from wurlitzer import pipes

    try:
        with pipes() as (out, err):
            try:
                with patch('builtins.input', return_value='') as mock:
                    exec_awscli(*args)
            except SystemExit as e:
                t_code = e.code
            else:
                # This should never happen...
                raise Exception("exec_awscli: Failed to raise SystemExit!")

        import sys
        cmd = ' '.join(sys.argv)

        t_out = out.read()
        t_err = err.read()

        # Must be closed explicitly otherwise we receive warnings
    finally:
        out.close()
        err.close()

    if calls:
        mock.assert_has_calls(calls)
        assert len(mock.call_args_list) == len(calls)

    return t_out, t_err, t_code, cmd
