tomcatmanager
=============

tomcatmanager is a command line tool and python library for managing a Tomcat
server.

What Can It Do?
---------------

This package installs a command line utility called ``tomcat-manager``. It's
easily scriptable using your favorite shell:

.. code-block:: bash

   $ tomcat-manager --user=ace --password=newenglandclamchowder \
   http://localhost:8080/manager deploy local sample.war /sampleapp
   $ echo $?
   0

There is also an interactive mode:

.. code-block:: bash

   $ tomcat-manager
   tomcat-manager>connect http://localhost:8080/manager ace newenglandclamchowder
   --connected to http://localhost:8080/manager as ace
   tomcat-manager>list
   Path                     Status  Sessions Directory
   ------------------------ ------- -------- ------------------------------------
   /                        running        0 ROOT
   /sampleapp               stopped        0 sampleapp##9
   /sampleapp               running        0 sampleapp##8
   /host-manager            running        0 /usr/share/tomcat8-admin/host-manage
   /manager                 running        0 /usr/share/tomcat8-admin/manager

And for the ultimate in flexibility, you can use the python package directly:

.. code-block:: python

   >>> import tomcatmanager as tm
   >>> tomcat = tm.TomcatManager()
   >>> r = tomcat.connect(url='http://localhost:8080/manager',
   ... user='ace', password='newenglandclamchowder')
   >>> tomcat.is_connected
   True
   >>> r = tomcat.stop('/someapp')
   >>> r.status_code == tm.status_codes.ok
   False
   >>> r.status_message
   'No context exists named /someapp'

System Requirements
-------------------

You'll need Python 3.4 or higher on macOS, Windows, or Linux.

The following Tomcat versions are supported:

- 7.0.x
- 8.0.x
- 8.5.x
- 9.0.x

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2

   install
   configuretomcat
   interactive
   commandline
   package
   api/index.rst
   contributing
   changelog
