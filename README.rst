tomcatmanager
=============

If you use Apache Tomcat for any sort of development work you’ve probably deployed lots of applications to it. There are a several ways to get your war files deployed:

- use the `Tomcat Manager <https://tomcat.apache.org/tomcat-8.5-doc/manager-howto.html>`_ application in your browser
- use the `Tomcat Ant Tasks <https://wiki.apache.org/tomcat/AntDeploy>`_ included with Tomcat
- use `Cargo <https://codehaus-cargo.github.io/>`_ and its plugins for ant and maven

Here's another way. tomcatmanager is a command line tool and python
library for managing a Tomcat server.


Quick Tour
----------

This package installs a command line utility called ``tomcat-manager``. It's easily scriptable using your favorite shell:

.. code-block:: bash

    $ tomcat-manager --user=ace --password=newenglandclamchowder \
      http://localhost:8080/manager deploy local sample.war /sampleapp
    $ echo $?
    0

There is also an interactive mode:

.. code-block:: bash

    $ tomcat-manager
    tomcat-manager>connect http://localhost:8080/manager ace newenglandclamchowder
    tomcat-manager>list
    Path                     Status  Sessions Directory
    ------------------------ ------- -------- ------------------------------------
    /                        running        0 ROOT
    /sampleapp               stopped        0 sampleapp##9
    /sampleapp               running        0 sampleapp##8
    /host-manager            running        0 /usr/share/tomcat8-admin/host-manage
    /manager                 running        0 /usr/share/tomcat8-admin/manager

And for the ultimate in flexibility, you can use the python library directly:

>>> import tomcatmanager as tm
>>> tomcat = tm.TomcatManager(url='http://localhost:8080/manager',
... userid='ace', password='newenglandclamchowder')
>>> tomcat.is_connected
True
>>> r = tomcat.stop('/')
>>> r.status_code == tm.codes.ok
False
>>> r.status_message
'No context exists named /sample'


Installation
------------

Install tomcatmanager using pip:

.. code-block:: bash

    $ pip install tomcatmanager


Tomcat Configuration
--------------------

This library and associated tools do their work via the Tomcat Manager
web application included in the Tomcat distribution. You will need to
configure authentication in ``tomcat-users.xml`` with access to the
``manager-script`` role:

.. code-block:: xml

    <tomcat-users>
    .....
        <role rolename="manager-script"/>
        <user username="ace" password="newenglandclamchowder" roles="manager-script"/>
    </tomcat-users>


Features
--------

The ``tomcat-manager`` command line tool supports the following commands:

- **list** - show all installed applications
- **serverinfo** - show information about the server, including tomcat version, OS version and architecture, and jvm version
- **statusxml** - show server status information in xml format
- **vminfo** - show diagnostic information about the jvm
- **sslconnectorciphers** - show ssl/tls ciphers configured for each connector
- **threaddump** - show a jvm thread dump
- **resources** - show the global jdni resources configured in tomcat
- **findleakers** - show tomcat applications that leak memory
- **sessions** - show active sessions for a particular tomcat application
- **expire** - expire idle sessions
- **start** - start a tomcat application that has been deployed but isn't running
- **stop** - stop a tomcat application and leave it deployed on the server
- **reload** - stop and start a tomcat application
- **deploy** - deploy a war file containing a tomcat application in the tomcat server
- **redeploy** - remove the application currently installed at a given path and install a new war file there
- **undeploy** - remove an application from the tomcat server
