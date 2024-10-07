Create Virtual Environment (Optional)
-------------------------------------

For testing, you may wish to install into a Python virtual environment.
We have created a bash script that will create a virtual environment
for testing ``awscli-login``. The script creates a standard Python
virtual environment with additional environment variables set so that
``aws`` and ``awscli-login`` look for configuration information within
the virtual environment. You may install this script with the following
command::

    $ wget https://raw.githubusercontent.com/techservicesillinois/awscli-login/master/scripts/mk_awscli_login_venv
    $ chmod +x mk_awscli_login_venv

To create the virtual environment type::

    $ ./mk_awscli_login_venv ENV_DIR

To activate it type::

    $ source ENV_DIR/bin/activate
    (awscli-login) $

Note that while inside the virtual environment your prompt will
appear different. It will be prefixed with the string ``(awscli-login)``.
To exit the virtual environment type the command ``deactivate``.

Pip Install
-----------

There can be issues installing with older versions of ``setuptools``,
so we recommend ensuring setuptools is up to date before installing.
To ensure that the dependencies installed are not test versions you
need to first install the package from test PyPI using the ``--no-deps``
flag then reinstall the package to get the dependencies from PyPI::

    $ pip install --upgrade setuptools
    $ pip install -i https://test.pypi.org/simple/ --no-deps awscli-login
    $ pip install awscli-login
