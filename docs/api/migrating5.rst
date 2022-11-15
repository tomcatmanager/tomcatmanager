Migrating to version 5.x
========================

Version 5.0 adds support for Python 3.10 and drops support for Python 3.6.


No API changes were made in this version, so you don't have to make any
changes to your code. The change in major version number with no API change
was done so that if you are using this library against a single version of
Tomcat, and you specify your ``setup.py`` dependency rules like::

   setup(
   ...
       install_requires=["tomcatmanager>=3,<4"]
   ...
   )

you won't have to worry about a future release of this software breaking your
configuration.
