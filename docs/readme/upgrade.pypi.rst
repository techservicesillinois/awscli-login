The module path for the plugin has changed. This requires a
configuration change before upgrading::

    $ aws configure set plugins.login awscli_login.plugin
    $ pip install --upgrade awscli-login

If you receive the following error from the ``aws`` command::

    AttributeError: module 'awscli_login' has no attribute 'awscli_initialize'

Then you will need to change the module path manually. To do so
open the awscli configuration file ``~/.aws/config``. Find or add
the ``plugins`` section and change or add the ``login`` key to have
the value ``awscli_login.plugin``::

    [plugins]
    login = awscli_login.plugin
