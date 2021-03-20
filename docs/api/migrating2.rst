Migrating to version 2.x
========================

Version 2.0 made some changes to the API for Tomcat Manager.


Application State
-----------------

In version 1.x, ``tomcatmanager.models.application_states`` was an instance of AttrDict, a class
from the `attrdict <https://github.com/bcj/AttrDict>`_ library. This library has been sunset: on python 3.9 it generates warnings from deprecated usage of the standard library. It will break
on python 3.10.

The :attr:`~tomcatmanager.models.TomcatApplication.state` attribute of the :class:`~tomcatmanager.models.TomcatApplication` class could
be used like this::

    import tomcatmanager as tm
    tomcat = tm.TomcatManager()
    tomcat.connect('http://localhost:8080/manager')
    r = tomcat.list()
    if r.ok:
      running = filter(lambda app: app.state == tm.application_states.running, r.apps)

In version 2.x, ``tomcatmanager.models.application_states`` has been replaced with an enum
called :class:`~tomcatmanager.models.ApplicationState`. The equivilent code in version 2.x is::

    import tomcatmanager as tm
    tomcat = tm.TomcatManager()
    tomcat.connect('http://localhost:8080/manager')
    r = tomcat.list()
    if r.ok:
        running = filter(lambda app: app.state == tm.ApplicationState.RUNNING, r.apps)

See :class:`~tomcatmanager.models.ApplicationState` for documentation on all the possible values.
