.. image:: https://github.com/techservicesillinois/awscli-login/workflows/CI/CD/badge.svg
   :target: https://github.com/techservicesillinois/awscli-login/actions?query=workflow%3ACI%2FCD
   :alt: Build Status

The awscli-login plugin allows retrieving temporary Amazon credentials
by authenticating against a SAML Identity Provider (IdP).  This
application is fully supported under Linux, macOS, and the `Windows
Subsystem for Linux <https://docs.microsoft.com/en-us/windows/wsl/about>`_.
Currently, Windows PowerShell, Command Prompt, and Git Shell for
Windows are supported with limitations (See `Windows Issues`_).

.. |--| unicode:: U+2013   .. en dash
.. contents:: Jump to:
   :depth: 1

Installation
============

The simplest way to install the awscli-login plugin is to use pip::

    $ pip install awscli-login

After awscli-login has been installed, run the following command
to enable the plugin::

    $ aws configure set plugins.login awscli_login

If you receive a bad interpreter error or other error please see
the `Known Issues`_ section below.

Getting Started
===============

Before using awscli-login to retrieve temporary credentials,
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

Advanced Configuration
======================

The plugin's configuration file (``~/.aws-login/config``) is an ini
file that supports more configuration options than is exposed via
the basic interactive configuration as seen in the `Getting Started`_
section. Each section corresponds to an `AWS named profile
<https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html>`__
just like the awscli's credentials file ``~/.aws/credentials``.

Here is a simple example configuration file::

    [default]
    ecp_endpoint_url = https://shib.uiuc.edu/idp/profile/SAML2/SOAP/ECP
    username = netid
    enable_keyring = True
    factor = auto

    [prod]
    username = netid
    ecp_endpoint_url = https://shib.uiuc.edu/idp/profile/SAML2/SOAP/ECP

and the corresponding awscli configuration file ``~/.aws/config`` ::

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
    better passed interactivally or by the ``--passcode`` command
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
    https://pypi.org/project/keyring for details). Set to True to
    enable::

        enable_keyring = True

    The password property and command line flag are ignored when
    the keyring is enabled.
disable_refresh:
    On POSIX systems tokens are refreshed automatically unless this
    property is set to True::

        disable-refresh = True
refresh
    How often the refresh process attempts to renew the STS credentials
    in seconds. When set to 0 the refresh process will refresh once
    90% of the time till expiration has transpired (Default 0)::

        refresh = 1800
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
to the online documentation. Options not avaliable as properties
are documented below.

options
```````

``--ask-password``
   Force prompt for password. This can be used to override the
   ``enable_keyring`` property.
``--force-refresh``
    Forces the refresh process to retrieve new credentials for the
    user selected role. If the refresh process is not running then
    a normal login will proceed after a warning.
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


Known Issues
============

Unable to authenticate after changing password
----------------------------------------------

After the user changes his IdP password, subsequent logins fail.
To remedy the situation, change the data stored in the keyring as follows:

    $ keyring set awscli_login username@hostname_of_your_IdP

You may be prompted for your user login password by your operating
system, depending on how your key store is configured.

Command line flag ``--ecp-endpoint-url`` error parsing parameter
----------------------------------------------------------------

If you encounter the following error it is because the awscli expects
urls passed as arguments to return a 200 on an HTTP GET (See
`aws-cli#4473 <https://github.com/aws/aws-cli/issues/4473>`_)::

    $ aws login --ecp-endpoint-url https://shibboleth.illinois.edu/idp/profile/SAML2/SOAP/ECP
    Error parsing parameter '--ecp-endpoint-url': Unable to retrieve https://shibboleth.illinois.edu/idp/profile/SAML2/SOAP/ECP: received non 200 status code of 500

This check can be disabled on a per profile basis using the following
command::

    $ aws configure set cli_follow_urlparam off

Windows issues
--------------

Auto-renewal is not supported under the Windows PowerShell, Command
Prompt, or Git Shell for Windows. Auto-renewal is supported under
the Windows Subsystem for Linux (WSL).

GitBash bad interpreter errors
``````````````````````````````

If you receive a bad interpreter error from the aws command it may
be because you have a space in the path of your Python interpreter::

    bash: /c/Users/me/AppData/Roaming/Python/Python38/Scripts/aws: c:\program: bad interpreter: No such file or directory

To fix this issue either reinstall your Python interpreter to a
path that does not contain a space and then reinstall the awscli
package, or more simply just define an alias in your bashrc file::

    alias aws='python $(which aws)'

Windows Subsystem for Linux bad interpreter error
`````````````````````````````````````````````````

If you receive a bad interpreter error from the aws command on
Windows Subsystem for Linux (WSL) it may be because the location
where the awscli is installed is not listed in the WSL's PATH before
the location of a Windows install of awscli::

    -bash: /mnt/c/Python39/Scripts/aws: c:\python39\python.exe^M: bad interpreter: No such file or directory

To remedy this issue please ensure that the location where the
awscli is installed in the WSL comes before the location of the
Windows install in the WSL PATH environment variable.
