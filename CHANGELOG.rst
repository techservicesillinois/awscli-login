Release History
===============

`1.0`_ 2025-03-07
-----------------

Added
`````
* --all flag to logout `#235`_
* support for Python 3.13 `#219`_
* support for awscli V2 `#106`_
* support for Python 3.12 `#180`_
* support for awscli credential_process `#132`_
* verify_ssl_certificate option `#102`_
* --save-http-traffic and --load-http-traffic `#119`_
* environment variable AWSCLI_LOGIN_ROOT `#121`_

Changed
```````
* override factor if --passcode is set at the cli `#220`_
* update ProfileNotFound error message `#109`_
* rename awscli_login plugin to awscli_login.plugin `#115`_
* invalid selection now issues a fatal error message `#71`_

Fixed
`````
* drop boto3 dependency that conflicts with awscliv2 `#73`_

Removed
```````
* refresh process `#156`_
* support for log directory `#155`_
* support for Python 3.8 `#219`_
* support for Python 3.7 `#169`_
* support for Python 3.6 `#110`_

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
.. _1.0: https://pypi.org/project/awscli-login/1.0/

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
.. _#73: https://github.com/techservicesillinois/awscli-login/pull/73
.. _#115: https://github.com/techservicesillinois/awscli-login/pull/115
.. _#121: https://github.com/techservicesillinois/awscli-login/pull/121
.. _#235: https://github.com/techservicesillinois/awscli-login/pull/235
.. _#219: https://github.com/techservicesillinois/awscli-login/pull/219
.. _#106: https://github.com/techservicesillinois/awscli-login/pull/106
.. _#180: https://github.com/techservicesillinois/awscli-login/pull/180
.. _#132: https://github.com/techservicesillinois/awscli-login/pull/132
.. _#102: https://github.com/techservicesillinois/awscli-login/pull/102
.. _#119: https://github.com/techservicesillinois/awscli-login/pull/119
.. _#220: https://github.com/techservicesillinois/awscli-login/pull/220
.. _#109: https://github.com/techservicesillinois/awscli-login/pull/109
.. _#156: https://github.com/techservicesillinois/awscli-login/pull/156
.. _#155: https://github.com/techservicesillinois/awscli-login/pull/155
.. _#169: https://github.com/techservicesillinois/awscli-login/pull/169
.. _#110: https://github.com/techservicesillinois/awscli-login/pull/110
