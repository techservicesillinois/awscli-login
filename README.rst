The awscli-login plugin allows retrieving temporary Amazon credentials by
authenticating against a SAML Identity Provider (IdP).
This application is supported under Linux, MacOS, and the `Windows Subsystem for Linux
<https://docs.microsoft.com/en-us/windows/wsl/about>`_.
Currently, Windows PowerShell, Command Prompt, and Git Shell
for Windows are not supported.

.. |--| unicode:: U+2013   .. en dash

Installation
------------

The simplest way to install the awscli-login plugin is to use pip::

    $ pip install awscli-login

After awscli-login has been installed, run the following command
to enable the plugin::

    $ aws configure set plugins.login awscli_login

Getting Started
-------------------

Before using awscli-login to retrieve temporary credentials, configure
one or more profiles for use with the plugin. To configure this
plugin, you must know the URL of the ECP Endpoint for your IdP.  If
you do not have this information, contact your IdP administrator.

Here is an example configuring the default profile for use with the University
of Illinois at Urbana-Champaign's IdP::

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
then ``Factor`` may be one of ``auto``, ``push``, ``passcode``,
``sms``, or ``phone``.  If ``factor`` is left blank, ``auto`` is
the default. The ``code`` is a Duo code useful for use with a
YubiKey, SMS codes, or other one-time codes.

If you have access to more than one role, you will be prompted to choose
one. For example::

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

To switch roles, first log out, then log in again selecting a different
role. Note that if you log in to the same IdP using the same username,
you will not be prompted for your password or Duo factor until
the IdP session expires::

    $ aws logout
    $ aws login
    Username [netid]: 
    Please choose the role you would like to assume:
        Account: 520135271718
            [ 0 ]: TestUser
            [ 1 ]: IAMUser
    Selection: 0

Advanced Example
-------------------

It is possible to be logged in to more than one role at the same
time using multiple profiles. For example, consider the following
configuration involving two profiles |--| one called ``prod``, and the other
``test``::

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

Known Issues
------------

**Unable to authenticate after changing password**

After the user changes his IdP password, subsequent logins fail.
To remedy the situation, change the data stored in the keyring as follows:

    $ keyring set awscli_login username@hostname_of_your_IdP

You may be prompted for your user login password by your operating
system, depending on how your key store is configured.

**Windows issues**

Windows PowerShell, Command Prompt, and Git Shell for Windows are not
currently supported because of problems with auto-renewal of AWS credentials,
and other known issues.
