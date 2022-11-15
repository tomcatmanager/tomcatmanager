Migrating to version 6.x
========================

Version 6.0 adds support for Python 3.11 and Tomcat 10.1. It drops support for
Tomcat 8.0.

No API changes were made in this version, so you don't have to make any changes to
your code. The change in major version number with no API change was done to prevent
your application breaking by a new release of this library, as long as you specify
your dependencies properly. See :ref:`package:Specifying As A Dependency` for more
information.

As of version 6.0.0, all supported Tomcat Manager web application versions support all
python API calls. Therefore, this version of the library will not raise
:exc:`~.models.TomcatNotImplementedError` exceptions. But, you should still check for
them. See :ref:`package:Differences in Tomcat Versions` for more information.
