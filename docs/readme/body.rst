Configuration
=============

After ``awscli-login`` has been installed, run the following command
to enable the plugin::

    $ aws configure set plugins.login awscli_login

If you receive a bad interpreter error or other error please see
the `Known Issues`_ section below. If it succeeds the AWS CLI
configuration file ``~/.aws/config`` should be updated with the
following section::

    [plugins]
    login = awscli_login

If you are using ``awscli-login`` with AWS CLI V2, proceed to the
next section. If you are still using AWS CLI V1, continue to the
`POSIX System Configuration`_ or `Windows System Configuration`_
section below.

AWS CLI V2 Configuration
------------------------

If you are configuring AWS CLI V2, the path to the site
packages directory where ``awscli-login`` resides must be supplied
as well. This can be looked up using the following command::

    $ pip show awscli-login
    Name: awscli-login
    Version: 1.0
    Summary: Plugin for the AWS CLI that retrieves and rotates credentials using SAML ECP and STS.
    Home-page:
    Author:
    Author-email: "David D. Riddle" <ddriddle@illinois.edu>
    License: MIT License
    Location: /usr/lib/python3.12/site-packages
    Requires: botocore, keyring, lxml, requests
    Required-by:

The ``Location`` field has the required path information, and must
be passed to ``aws configure``::

    $ aws configure set plugins.cli_legacy_plugin_path <<PASTE ``Location`` HERE>>

Note: If your output matched the example above, you would paste in
``/usr/lib/python3.12/site-packages``.

On POSIX systems such as macOS and Linux the preceding can be set
more easily using the following one-liner::

    $ aws configure set plugins.cli_legacy_plugin_path $(pip show awscli-login | sed -nr 's/^Location: (.*)/\1/p')

If it succeeds the AWS CLI configuration file ``~/.aws/config``
should be updated with the following section::

    [plugins]
    login = awscli_login
    cli_legacy_plugin_path = /usr/lib/python3.12/site-packages

Note that ``cli_legacy_plugin_path`` should point to the same value
as given in the ``Location`` field given by ``pip show awscli-login``
above.

POSIX System Configuration
--------------------------

The command or script ``aws-login`` must be on your ``$PATH``::

    $ which aws-login

If it is not on your path you can use the following command to determine
its location::

    $ pip show awscli-login --files
    ...
    Location: /Users/USERNAME/Library/Python/3.9/lib/python/site-packages
    ...
    Files:
      ../../../bin/aws-login

Look for the path to the file ``aws-login`` under the ``Files`` field.
Note that the path is relative to the ``site-packages``
path which can be found in the ``Location`` field. In the example above,
the desired path is::

    /Users/USERNAME/Library/Python/3.9/bin

Add this path to your system path in your shell's config file. After updating
your path, verify that ``aws-login`` appears on your PATH::

    $ which aws-login
    /Users/USERNAME/Library/Python/3.9/bin/aws-login

Once your system path is configured, skip to the `Upgrade`_ section
if you are upgrading from version ``0.2b1``,  or straight to the
`Getting Started`_ section otherwise.

Windows System Configuration
----------------------------

The command or script ``aws-login`` must be on your ``$PATH``::

    PS> Get-Command aws-login
    Get-Command : The term 'aws-login' is not recognized as the name of a cmdlet, function, script file, or operable program. Check the spelling of the name, or
    if a path was included, verify that the path is correct and try again.
    At line:1 char:1
    + Get-Command foo
    + ~~~~~~~~~~~~~~~
        + CategoryInfo          : ObjectNotFound: (foo:String) [Get-Command], CommandNotFoundException
        + FullyQualifiedErrorId : CommandNotFoundException,Microsoft.PowerShell.Commands.GetCommandCommand

If it is not on your path you can use the following command to determine
its location::

    PS> pip show awscli-login --files
    ...
    Location: C:\Users\USERNAME\AppData\Roaming\Python\Python312\site-packages
    ...
    Files:
    ..\Scripts\aws-login.exe
    ...

Look for the path to the file ``aws-login.exe`` under the ``Files`` field.
Note that the path is relative to the ``site-packages``
path which can be found in the ``Location`` field. In the example above,
the desired path is::

    C:\Users\USERNAME\AppData\Roaming\Python\Python312\Scripts

Detailed instructions on how to make changes to your
path on Windows can be found
`here <https://www.wikihow.com/Change-the-PATH-Environment-Variable-on-Windows>`__.
After setting your PATH, verify that ``aws-login`` appears on it::

    PS> Get-Command aws-login

    CommandType     Name                                               Version    Source
    -----------     ----                                               -------    ------
    Application     aws-login.exe                                      0.0.0.0    C:\Users\USERNAME\AppData\Roaming\Python\Python312\Scripts\aws-login.exe

Once your system path is configured, skip to the `Upgrade`_ section
if you are upgrading from version ``0.2b1``,  or straight to the
`Getting Started`_ section otherwise.

Upgrade
=======

If you are upgrading from ``awscli-login`` version ``0.2b1`` or
earlier, please follow the `Installation`_ instructions above, then
proceed to the `Getting Started`_ section below to reconfigure your
profiles which is required.

Reconfiguration is required because in previous versions of
``awscli-login`` credentials were directly stored in AWS CLI's
credentials file ``~/.aws/credentials``. This is no longer the case.
Now each profile contains a reference to the ``aws-login`` script.

Previously ``~/.aws/credentials`` would have looked looked like this
after a log out::

    [default]
    aws_access_key_id = abc
    aws_secret_access_key = def
    aws_session_token = ghi
    aws_security_token = ghi

After a reconfiguration, the example ``~/.aws/credentials`` file
above should look like this::

    [default]
    credential_process = aws-login --profile default

If you attempt to log into a profile that has not been reconfigured
you will receive the following error message::

    $ aws login
    Credential process is not set for current profile "foo".
    Reconfigure using:

    aws login configure

Getting Started
===============

Before using ``awscli-login`` to retrieve temporary credentials,
optionally configure one or more `named profiles
<https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html>`__
for use with the plugin. To configure this plugin, you must know
the URL of the ECP Endpoint for your IdP.  If you do not have this
information, contact your IdP administrator.

Here is an example configuring the default profile for use with the
University of Illinois at Urbana-Champaign's IdP::

    $ aws login configure
    ECP Endpoint URL [None]: https://shibboleth.illinois.edu/idp/profile/SAML2/SOAP/ECP
    Username [None]:
    Enable Keyring [False]:
    Duo Factor [None]:
    Role ARN [None]:

To log in, type the following command::

    $ aws login
    Username [username]: netid
    Password: ********
    Factor: passcode
    Code: 123456789

The ``username`` and ``password`` are the values needed to authenticate
against the IdP configured for the selected profile.  The ``factor``
is only required if your IdP requires Duo for authentication.  If
it does not, leave ``factor`` blank. If your IdP does require Duo
then ``factor`` may be one of ``auto``, ``push``, ``passcode``,
``sms``, or ``phone``.  If ``factor`` is left blank, ``auto`` is
the default. The ``code`` is a Duo code useful for use with a
YubiKey, SMS codes, or other one-time codes.

If you have access to more than one role, you will be prompted to
choose one. For example::

    $ aws login
    Username [username]: netid
    Password: ********
    Factor:
    Please choose the role you would like to assume:
        Account: 978517677611
            [ 0 ]: Admin
        Account: 520135271718
            [ 1 ]: ReadOnlyUser
            [ 2 ]: S3Admin
    Selection: 2

To switch roles, first log out, then log in again selecting a
different role. Note that if you log in to the same IdP using the
same username, you will not be prompted for your password or Duo
factor until the IdP session expires::

    $ aws logout
    $ aws login
    Username [netid]:
    Please choose the role you would like to assume:
        Account: 520135271718
            [ 0 ]: TestUser
            [ 1 ]: IAMUser
    Selection: 0

Advanced Usage
==============

It is possible to be logged in to more than one role at the same
time using multiple `named profiles
<https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html>`__.
For example, consider the following configuration involving two
profiles |--| one called ``prod``, and the other ``test``::

    $ aws --profile prod login configure
    ECP Endpoint URL [None]: https://shibboleth.illinois.edu/idp/profile/SAML2/SOAP/ECP
    Username [None]: netid
    Enable Keyring [False]: True
    Duo Factor [None]: auto
    Role ARN [None]: arn:aws:iam::999999999999:role/Admin

    $ aws --profile test login configure
    ECP Endpoint URL [None]: https://shibboleth.illinois.edu/idp/profile/SAML2/SOAP/ECP
    Username [None]: netid
    Enable Keyring [False]: True
    Duo Factor [None]: passcode
    Role ARN [None]: arn:aws:iam::111111111111:role/Admin

This example involves several advanced features. First, we are
setting the username, factor, and role. This means we will not be
prompted for this information when logging in to these two profiles.
In addition, we are using a keyring. On the first login using one
of the profiles, the user will be prompted for his password.  On
subsequent logins the user will not be prompted for his password
because it has been stored in a secure keyring.

For example, when we initially log in to prod::

    $ export AWS_PROFILE=test
    $ aws login
    Password: ********
    Code: 123456789

We are only prompted for the password and code. We're prompted for
the password because this is the initial login, and the code because
this profile is configured for use with a passcode device such as
a YubiKey. We are now no longer prompted when we log in to test::

    $ aws --profile prod login

Even if the IdP session has expired in this case, we will not be
prompted for a password because it is stored in the keyring. The
user will receive either a phone call or a push to the default
Duo device.

For an easier way to switch between multiple profiles, consider adding a
shell function like this in your shell's start-up script::

    $ awsprofile () { [ "$1" ] && export AWS_PROFILE=$1 || unset AWS_PROFILE; }

This function should work on any Bourne compatible
shell (bash, zsh, ksh, dash, etc).
Using this function, you can set the profile for ``login`` and other ``aws``
commands to use::

    $ awsprofile prod
    $ aws login
    $ aws s3 ls
    $ awsprofile test
    $ aws login
    $ aws s3 ls

The above would log into the prod profile and do an s3 ls then switch to
the test profile and do an s3 ls in that profile. You're now logged into
both profiles simultaneously and can switch between them by issuing
``awsprofile`` commands. Additionally, you can run ``awsprofile`` without any
profile name to clear ``$AWS_PROFILE``.

Advanced Configuration
======================

The plugin's configuration file (``~/.aws-login/config``) is an ini
file that supports more configuration options than is exposed via
the basic interactive configuration as seen in the `Getting Started`_
section. Each section corresponds to an `AWS named profile
<https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html>`__
just like the AWS CLI's credentials file ``~/.aws/credentials``.

Here is a simple example configuration file::

    [default]
    ecp_endpoint_url = https://shib.uiuc.edu/idp/profile/SAML2/SOAP/ECP
    username = netid
    enable_keyring = True
    factor = auto

    [prod]
    username = netid
    ecp_endpoint_url = https://shib.uiuc.edu/idp/profile/SAML2/SOAP/ECP

and the corresponding AWS CLI configuration file ``~/.aws/config`` ::

    [plugins]
    login = awscli_login

    [default]
    region = us-east-2
    output = json

    [profile prod]
    region = us-east-2
    output = json

All configuration options are documented below in the `properties`_
section.

Properties
----------

Each property can be overridden at the command line using a flag.
See the online documentation for further details by running ``aws
login help``.

..
    Order matches cli help found __init__.py:class Login:ARG_TABLE

ecp_endpoint_url
    The ECP endpoint URL of the IdP. This is the only required
    property::

        ecp_endpoint_url = https://shibboleth.illinois.edu/idp/profile/SAML2/SOAP/ECP
username
    The username to use on login to the IdP. If the username is not
    supplied the user will be prompted::

        username = netid
password
    The password to use on login to the IdP. If the password is not
    supplied the user will be prompted. It is not recommended to
    use this property. Instead supply the password interactively
    or use the keyring for secure storage::

        password = secret

    The password property and command line flag are ignored if the
    keyring is enabled. When this happens a warning is issued.
factor
    The `Duo factor <https://duo.com/docs/authapi#/auth>`_ to use
    on login::

        factor = auto

    The following values are currently supported:

    +------------------------+-------------------------------------------+
    | factor                 |                                           |
    +========================+===========================================+
    | ``auto``               | authenticates with ``push`` if available, |
    |                        | otherwise fallbacks to ``phone``          |
    +------------------------+-------------------------------------------+
    | ``push``               | authenticates with Duo Push               |
    +------------------------+-------------------------------------------+
    | ``passcode``           | authenticates the user with a user        |
    |                        | supplied code from a hardware token,      |
    |                        | Duo Mobile, or bypass code                |
    +------------------------+-------------------------------------------+
    + ``sms``                | sends a batch of SMS passcodes to the user|
    +------------------------+-------------------------------------------+
    | ``phone``              | Authenticates with phone callback         |
    +------------------------+-------------------------------------------+

    To login using ``sms``, requires two attempts. The first attempt
    will send SMS passcodes, and return authentication failed. The
    second attempt will use the passcodes::

        $ aws login --factor sms
        Authentication failed!
        $ aws login --factor passcode
        Code: 829437
passcode
    A bypass code or Duo `passcode
    <https://duo.com/product/multi-factor-authentication-mfa/authentication-methods/tokens-and-passcodes>`_
    generated by Duo Mobile, SMS, or a hardware token can be set
    using the passcode property::

        passcode = 829437

    It is not recommended to store a passcode in your configuration
    file since a passcode can only be used once. A passcode is
    better passed interactively or by the ``--passcode`` command
    line flag.
role_arn
    The role ARN to select. If the IdP returns a single role it is
    autoselected::

        role_arn = arn:aws:iam::999999999999:role/Admin
enable_keyring
    By default the keyring is not used for password storage. The
    keyring is implemented using the Python module `keyring
    <https://pypi.org/project/keyring/>`_, and supports various
    secure backends such as the macOS Keychain, Windows Credential
    Locker, and Linux keyrings. Additional, system configuration
    may be required to use a keyring on Linux systems (See
    https://pypi.org/project/keyring for details). For an example of this
    on WSL using the Windows Credential Store, see
    `Keyrings with WSL and Windows Credential Store`_ below.

    Set to True to
    enable::

        enable_keyring = True

    The password property and command line flag are ignored when
    the keyring is enabled.
duration
    Set the time in seconds that the STS token will last. The token
    lasts for the duration you specify, or until the time specified
    by the IdP, whichever is shorter. The default is an hour, and
    the minimum is 15 minutes (See `AssumeRoleWithSAML
    <https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRoleWithSAML.html>`_
    for details)::

        duration = 3600
http_header_factor
    HTTP Header to store the user's Duo factor::

        http_header_factor = X-Shibboleth-Duo-Factor
http_header_passcode
    HTTP Header to store the user's passcode::

        http_header_passcode = X-Shibboleth-Duo-Passcode

verify_ssl_certificate
    Whether to verify the SSL certificate from the IdP. Defaults to true::

        verify_ssl_certificate = True

Command line arguments
======================

The plugin supports two subcommands `login`_ and `logout`_.

login
-----

Detailed online documentation can be accessed using the following
command::

    $ aws login help

All `properties`_, except for enable_keyring, can be overridden
with a corresponding command line option. Properties that contain
an underscore will have a corresponding option with hyphens, for
example the property ecp_endpoint_url becomes ``--ecp-endpoint-url``.
For details on these options see the documentation above or refer
to the online documentation. Options not available as properties
are documented below.

options
```````

``--ask-password``
   Force prompt for password. This can be used to override the
   ``enable_keyring`` property.
``--force-refresh``
    Forces retrieval of new credentials for the user selected role.
``--verbose``
    Display verbose output. The flag can be repeated up to three
    times. Each time it is repeated more detailed information is
    returned.


configure
`````````

See `Getting Started`_ and online documentation for documentation on this
subcommand::

    $ aws login configure help

options
"""""""

``--verbose``
    Display verbose output. The flag can be repeated up to three
    times. Each time it is repeated more detailed information is
    returned.


logout
------

See `Getting Started`_ and online documentation for documentation on this
subcommand::

    $ aws logout help

options
```````

``--verbose``
    Display verbose output. The flag can be repeated up to three
    times. Each time it is repeated more detailed information is
    returned.

Environment Variables
=====================

``AWSCLI_LOGIN_ROOT``
    The environment variable ``AWSCLI_LOGIN_ROOT`` may be used to
    change the location of the plugin's configuration files from
    the default (``~/.aws-login``), rooted in the user's home
    directory, to a location rooted at the path
    ``$AWSCLI_LOGIN_ROOT/.aws-login``.  For example, if
    ``AWSCLI_LOGIN_ROOT`` is set to ``/tmp`` then the plugin will
    look for configuration files in (``/tmp/.aws-login/``).

Keyrings with WSL and Windows Credential Store
=====================================

If running under WSL, you may wish to store credentials in the Windows
Credential Store in the Windoes host operating system and access them
from within WSL. To do this, first install Python on the Windows
host operating system if not already installed. You can do this from
the Microsoft Store or using Winget, or you can download the installer
directly from the Python official site. The Python keyring module
will need to beinstalled on the Windows Python instance. From a
Windows command prompt, run::

    C:\> pip install keyring

Next, inside WSL, install the keyring-pybridge module:

    $ pip install keyring-pybridge

Still in WSL, Set the PYTHON_KEYRING_BACKEND environment variable to
tell Python to use the pybridge keyring backend. This is shell
specific but might look like:

    $ export PYTHON_KEYRING_BACKEND=keyring_pybridge.PyBridgeKeyring

Finally, set the KEYRING_PROPERTY_PYTHON environment variable to point
to the Windows Python executable. If you need to find the full path
to this executable, run this from the **Windows command prompt**:

    C:\> where python.exe

Inside WSL, set this environment variable like this. If Python is at
c:\path\to\python.exe, translate the path like this:

    $ export KEYRING_PROPERTY_PYTHON='/mnt/c/path/to/python.exe'

You'll probably want to set these environment variables in your
shell start-up script. Once set, Python keyring in WSL will talk to 
Python keyring in the Windows host OS which, by default, uses the
Windows Credential Store for keyring storage.

Known Issues
============

Module not found error
----------------------

When trying to run an ``aws`` or ``aws-login`` command if you receive
``ModuleNotFoundError``::

    # aws login configure
    Traceback (most recent call last):
      File "/usr/local/bin/aws", line 27, in <module>
        sys.exit(main())
                 ^^^^^^
      File "/usr/local/bin/aws", line 23, in main
        return awscli.clidriver.main()
               ^^^^^^^^^^^^^^^^^^^^^^^
      File "/usr/local/lib/python3.12/site-packages/awscli/clidriver.py", line 73, in main
        driver = create_clidriver()
                 ^^^^^^^^^^^^^^^^^^
      File "/usr/local/lib/python3.12/site-packages/awscli/clidriver.py", line 82, in create_clidriver
        load_plugins(
      File "/usr/local/lib/python3.12/site-packages/awscli/plugin.py", line 44, in load_plugins
        modules = _import_plugins(plugin_mapping)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "/usr/local/lib/python3.12/site-packages/awscli/plugin.py", line 61, in _import_plugins
        module = __import__(path, fromlist=[module])
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ModuleNotFoundError: No module named '/usr/local/lib/python3'

You may be running AWS CLI V1 while the ``awscli-plugin`` is
configured for AWS CLI V2. This can be confirmed by running::

    $ AWS_CONFIG_FILE='/dev/null' aws --version
    aws-cli/1.37.13

If you wish to continue to use AWS CLI V1, you will need to
remove or hash out the key-value pair ``cli_legacy_plugin_path``::

    [plugins]:
    login = awscli_login
    # cli_legacy_plugin_path = /usr/local/lib/python3.12/site-packages

When you upgrade to AWS CLI V2, it will be necessary to add the
key-value pair ``cli_legacy_plugin_path`` back.

Unable to authenticate after changing password
----------------------------------------------

After the user changes his IdP password, subsequent logins fail.
To remedy the situation, change the data stored in the keyring as follows::

    $ keyring set awscli_login username@hostname_of_your_IdP

You may be prompted for your user login password by your operating
system, depending on how your key store is configured.

Command line flag ``--ecp-endpoint-url`` error parsing parameter
----------------------------------------------------------------

If you encounter the following error it is because the AWS CLI expects
URLs passed as arguments to return a 200 on an HTTP GET (See
`aws-cli#4473 <https://github.com/aws/aws-cli/issues/4473>`_)::

    $ aws login --ecp-endpoint-url https://shibboleth.illinois.edu/idp/profile/SAML2/SOAP/ECP
    Error parsing parameter '--ecp-endpoint-url': Unable to retrieve https://shibboleth.illinois.edu/idp/profile/SAML2/SOAP/ECP: received non 200 status code of 500

This check can be disabled on a per profile basis using the following
command::

    $ aws configure set cli_follow_urlparam off

GitBash bad interpreter errors
------------------------------

If you receive a bad interpreter error from the ``aws`` command it may
be because you have a space in the path of your Python interpreter::

    bash: /c/Users/me/AppData/Roaming/Python/Python38/Scripts/aws: c:\program: bad interpreter: No such file or directory

To fix this issue either reinstall your Python interpreter to a
path that does not contain a space and then reinstall the AWS CLI
package, or more simply just define an alias in your `~/.bashrc` file::

    alias aws='python $(which aws)'

Windows Subsystem for Linux bad interpreter error
-------------------------------------------------

If you receive a bad interpreter error from the ``aws`` command on
Windows Subsystem for Linux (WSL) it may be because the location
where the AWS CLI is installed is not listed in the WSL's PATH before
the location of a Windows install of AWS CLI::

    -bash: /mnt/c/Python39/Scripts/aws: c:\python39\python.exe^M: bad interpreter: No such file or directory

To remedy this issue please ensure that the location where the
AWS CLI is installed in the WSL comes before the location of the
Windows install in the WSL PATH environment variable.


lxml import errors on macOS
---------------------------

On M1 and M2 Apple MacBooks you may receive the following error at runtime::

    ImportError: dlopen(/Users/ddriddle/.pyenv/versions/3.8.16/lib/python3.8/site-packages/lxml/etree.cpython-38-darwin.so, 0x0002): symbol not found in flat namespace '_exsltDateXpathCtxtRegister'

This can be fixed by removing and compiling lxml::

    pip uninstall lxml
    PIP_NO_BINARY=lxml pip install lxml
