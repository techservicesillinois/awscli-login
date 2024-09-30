.. include:: readme/header.rst

Installation
============

If you are upgrading from ``awscli-login`` version ``0.2b1`` or earlier,
please logout then uninstall ``awscli-login`` and ``awscli`` to
ensure a smooth upgrade::

    $ aws logout
    $ pip uninstall awscli-login awscli

Before installing ``awscli-login`` you need to install `AWS CLI`_ V1 or V2.
Instructions for installing V2 can be found on Amazon's website `here`_:

.. _here: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
.. _AWS CLI: https://aws.amazon.com/cli/

AWS CLI V1 can be installed using ``pip install awscli``.

.. include:: readme/install.{{ ENV }}.rst

.. include:: readme/body.rst
