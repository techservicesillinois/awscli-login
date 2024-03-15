The simplest way to install the awscli-login plugin is to use pip.

There can be issues installing with older versions of `setuptools`, 
so we recommend ensuring setuptools is up to date before installing::

    $ pip install --upgrade setuptools
    $ pip install awscli-login

After awscli-login has been installed, run the following command
to enable the plugin::

    $ aws configure set plugins.login awscli_login

If you receive a bad interpreter error or other error please see
the `Known Issues`_ section below.
