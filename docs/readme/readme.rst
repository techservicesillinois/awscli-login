.. include:: readme/header.rst

Installation
============

If you are upgrading from ``awscli-login`` version ``0.2b1`` or earlier,
please log out, then uninstall ``awscli-login`` and ``awscli`` to
ensure a smooth upgrade::

    $ aws logout
    $ pip uninstall awscli-login awscli

Before installing ``awscli-login`` you need to install `AWS CLI`_
V1 or V2. Instructions for installing V2 can be found on Amazon's
`website`_. AWS CLI V1 can be installed using ``pip install awscli``.

.. _website: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
.. _AWS CLI: https://aws.amazon.com/cli/


Please note that if you have both AWS CLI V1 and V2 installed, and
wish to use the same configuration file ``~/.aws/config`` for both
versions, then you must configure the ``awscli-login`` plugin for
V1. If you configure it for V2, you will encounter errors when
running V1 (See `Module not found error`_).

.. include:: readme/install.{{ ENV }}.rst

.. include:: readme/body.rst
