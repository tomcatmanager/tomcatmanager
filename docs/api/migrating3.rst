Migrating to version 3.x
========================

Version 3.0 made some meaningful and important changes to the API for Tomcat Manager.


- TomcatManager.user is now a read-only property instead of a read-write attribute,
  use connect() to set this value
- TomcatManager.url is now a read-only property
  instead of a read-write attribute, use connect() to set this value

- new class TomcatMajorMinor
- new attribute TomcatManager.tomcat_major_minor, if we are connected contains the
  indication of which major version of tomcat the server is running
  - usage, if tm.is_connected(): then tm.tomcat_major_minor
  - usage, r = tm.connect(), if r.ok: then tm.tomcat_major_minor

- TomcatManager.connect() now returns information about the server in the response
  (same as serverinfo())


