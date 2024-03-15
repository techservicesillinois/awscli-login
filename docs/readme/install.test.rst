The simplest way to install the awscli-login plugin is to use pip.

There can be issues installing with older versions of `setuptools`,
so we recommend ensuring setuptools is up to date before installing.
To ensure that the dependencies installed are not test versions you
need to first install the package from test PyPI using the `--no-deps`
flag then reinstall the package to get the dependencies from PyPI::

    $ pip install --upgrade setuptools
    $ pip install -i https://test.pypi.org/simple/ --no-deps awscli-login
    $ pip install awscli-login

After awscli-login has been installed, run the following command
to enable the plugin::

    $ aws configure set plugins.login awscli_login

If you receive a bad interpreter error or other error please see
the `Known Issues`_ section below.
