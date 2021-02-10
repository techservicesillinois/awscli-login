Release History
===============

`Unreleased`_
-------------

Changed
```````

* invalid selection now issues a fatal error message `#71`_

`0.2b1`_ 2021-02-04
---------------------

Added
`````
* support for Python 3.9

Changed
```````
* traceback no longer displayed on error `#59`_

Fixed
`````
* cli flags unable to set logically False values `#64`_
* broken force-refresh flag `#62`_
* broken refresh property and flag `#61`_
* broken passcode property and flag `#60`_
* broken password property and flag `#58`_
* module 'os' has no attribute 'fchmod' error on Windows `#11`_ `#24`_
* AuthnRequest IssueInstant generated is invalid due to missing
  timezone `#41`_

Removed
```````
* tests from package `#66`_
* ability to set verbose property in config file `#57`_
* unimplemented entity-id command line flag `#53`_
* broken automatic refresh support on Windows systems `#1`_

`0.1.0a6`_ 2019-09-19
-----------------------

Added
`````
* option to change HTTP header factor & passcode sent to IdP
* Shibboleth IdP 3.4 Duo plugin support `#25`_
* aws_security_token to credentials written/removed (boto2) `#22`_
* disable_refresh and duration options `#22`_

Changed
```````
* warn if unknown property is found in profile configuration

`0.1.0a5`_ 2018-05-19
-----------------------

Fixed
`````
* setting role arn now works as expected `#9`_

`0.1.0a4`_ 2018-05-12
-----------------------
* Initial public release

.. _Unreleased: https://test.pypi.org/project/awscli-login/

.. _0.1.0a4: https://pypi.org/project/awscli-login/0.1.0a4/
.. _0.1.0a5: https://pypi.org/project/awscli-login/0.1.0a5/
.. _0.1.0a6: https://pypi.org/project/awscli-login/0.1.0a6/
.. _0.2b1: https://pypi.org/project/awscli-login/0.2b1/

.. _#1: https://github.com/techservicesillinois/awscli-login/issues/1
.. _#9: https://github.com/techservicesillinois/awscli-login/issues/9
.. _#11: https://github.com/techservicesillinois/awscli-login/issues/11
.. _#22: https://github.com/techservicesillinois/awscli-login/pull/22
.. _#24: https://github.com/techservicesillinois/awscli-login/pull/24
.. _#25: https://github.com/techservicesillinois/awscli-login/issues/25
.. _#41: https://github.com/techservicesillinois/awscli-login/issues/41
.. _#53: https://github.com/techservicesillinois/awscli-login/pull/53
.. _#57: https://github.com/techservicesillinois/awscli-login/pull/57
.. _#58: https://github.com/techservicesillinois/awscli-login/pull/58
.. _#59: https://github.com/techservicesillinois/awscli-login/pull/59
.. _#60: https://github.com/techservicesillinois/awscli-login/pull/60
.. _#61: https://github.com/techservicesillinois/awscli-login/pull/61
.. _#62: https://github.com/techservicesillinois/awscli-login/pull/62
.. _#64: https://github.com/techservicesillinois/awscli-login/pull/64
.. _#66: https://github.com/techservicesillinois/awscli-login/pull/66
.. _#71: https://github.com/techservicesillinois/awscli-login/pull/71
