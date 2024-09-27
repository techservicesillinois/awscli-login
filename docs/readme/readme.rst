.. include:: readme/header.rst

Installation
============

The simplest way to install the ``awscli-login`` plugin is to use pip.

.. include:: readme/install.{{ ENV }}.rst

After ``awscli-login`` has been installed, run the following command
to enable the plugin::

    $ aws configure set plugins.login awscli_login

If you receive a bad interpreter error or other error please see
the `Known Issues`_ section below.

.. include:: readme/body.rst
