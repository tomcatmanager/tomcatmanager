Migrating to version 2.x
========================

Version 2.0 made some changes to the API for Tomcat Manager.


Status Codes
------------

In version 1.x ``tomcatmanager.models.status_codes`` was an instance of AttrDict,
a class from the `attrdict <https://github.com/bcj/AttrDict>`_ library. This
library has been sunset: on python 3.9 it generates warnings from deprecated
usage of the standard library. It will break on python 3.10.

Most methods on :class:`~tomcatmanager.tomcat_manager.TomcatManager` return a
:class:`.TomcatManagerResponse`. You should be using the
:attr:`.TomcatManagerResponse.ok` property to determine
whether your command completed successfully. This method checks both the HTTP
response code, as well as parsing the status text received from the `Tomcat
Manager web application
<https://tomcat.apache.org/tomcat-10.0-doc/manager-howto.html>`_. If your code
does this, migrating to 2.x will be very easy, because you won't have to change
much of anything. The following code works in both 1.x and 2.x::

    import tomcatmanager as tm
    tomcat = tm.TomcatManager()
    tomcat.connect('http://localhost:8080/manager')
    try:
        r = tomcat.server_info()
        r.raise_for_status()
        if r.ok:
            print(r.server_info.os_name)
        else:
            print(f"Error: {r.status_message}")
    except Exception as err:
        # handle exception
        pass

If you are doing alternative checking like this::

    import tomcatmanager as tm
    tomcat = tm.TomcatManager()
    tomcat.connect('http://localhost:8080/manager')
    try:
        r = tomcat.server_info()
        r.raise_for_status()
        if r.status_code == tm.status_codes.notfound:
            print("Tomcat Manager web application was not found")

you might consider this a good opportunity to update your code to check
:attr:`.TomcatManagerResponse.ok` instead. If that doesn't work for you, then
you'll have to change it to be something like this::

    import tomcatmanager as tm
    tomcat = tm.TomcatManager()
    tomcat.connect('http://localhost:8080/manager')
    try:
        r = tomcat.server_info()
        r.raise_for_status()
        if r.status_code == tm.StatusCode.NOTFOUND:
            print("Tomcat Manager web application was not found")

See :class:`.StatusCode` for the list of all available status codes.


Application State
-----------------

In version 1.x, ``tomcatmanager.models.application_states`` was an instance of
AttrDict, a class from the `attrdict <https://github.com/bcj/AttrDict>`_
library. This library has been sunset: on python 3.9 it generates warnings from
deprecated usage of the standard library. It will break on python 3.10.

The :attr:`~.TomcatApplication.state` attribute of the
:class:`.TomcatApplication` class could be used like
this::

    import tomcatmanager as tm
    tomcat = tm.TomcatManager()
    tomcat.connect('http://localhost:8080/manager')
    r = tomcat.list()
    if r.ok:
      running = filter(lambda app: app.state == tm.application_states.running, r.apps)

In version 2.x, ``tomcatmanager.models.application_states`` has been replaced
with an enum called :class:`.ApplicationState`. The
equivilent code in version 2.x is::

    import tomcatmanager as tm
    tomcat = tm.TomcatManager()
    tomcat.connect('http://localhost:8080/manager')
    r = tomcat.list()
    if r.ok:
        running = filter(lambda app: app.state == tm.ApplicationState.RUNNING, r.apps)

See :class:`.ApplicationState` for documentation on all the possible values.


