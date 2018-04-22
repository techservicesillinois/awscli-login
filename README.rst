Project Description
-------------------

awscli-login is a plugin that allows retreiving temporary Amazon
credentials by authenticating against a SAML Identity Provider
(IdP).

Installation
------------

The simplest way to install awscli-login plugin is to use pip::

   $ pip install awscli-login

After the awscli-login has been installed run the following command
to enable the plugin::

	$ aws configure set plugins.login awscli_login

Getting Started
-------------------

Before using awscli-login to retrieve temporary credentials it is
necessary to configure one or more profiles for use with the plugin. To
configure this plugin you must know the URL of the ECP Endpoint for your IdP.
If you do not have this information contact your IdP administrator.

Here is an example configuring the default profile for use with the University
of illinois at Urbana-Champaign's IdP::

    $ aws login configure
    ECP Endpoint URL [None]: https://shibboleth.illinois.edu/idp/profile/SAML2/SOAP/ECP
    Username [None]: 
    Enable Keyring [False]: 
    Duo Factor [None]: 
    Role ARN [None]:

To login type the following command::

    $ aws login
    Username [username]: netid
    Password: ********
    Factor: passcode
    Code: 123456789

The username and password prompted for are the values needed to
authenticate against the IdP configured for the selected profile.
Factor is only required if your IdP requires Duo for authentication.
If it does not then leave Factor blank. If your IdP does require
Duo then Factor may be one of auto, push, passcode, sms, or phone.
If left blank auto is the default. Code is a Duo code useful for
use with a YubiKey, SMS codes, or other one-time use Duo codes.

If you have access to more than role you will be prompted to choice
a role. For example::

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

To switch roles first logout, then login again selecting a different
role, note that if you login to the same IdP using the same username
then you will not be prompted for your password or Duo factor until
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
time using multiple profiles. For example consider the following
configuration involving two profiles one called prod and the other
test::

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

This example involves several advanced features. First we are setting
the username, factor, and role this means that we will not be
prompted for this information when logging into these two profiles.
In addition, we are using a Keyring. On the first login using one
of the profiles the user will be prompted for his password but on
subsequent logins the user will not be prompted for his password
because it has been stored in a secure keyring.

For example when we initially login to prod::

    $ export AWS_PROFILE=test
    $ aws login
    Password: ********
    Code: 123456789

We are only prompted for the password and code. The password because
this is the initial login, the code because this profile is configured
for use with a passcode device such as a YubiKey. Now when we login
in to test we are prompted for nothing::

    $ aws --profile prod login

Even if the IdP session has expired in this case we will not be
prompted for a password because it is stored in the Keyring. The
user will recieve either a phone call or a push to the default
device configured for Duo to permit authenticating.
