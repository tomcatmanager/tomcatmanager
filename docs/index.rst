tomcatmanager
=============

tomcatmanager is a command line tool and python library for managing a Tomcat
server.

What Can It Do?
---------------

This package installs a command line utility called ``tomcat-manager``. It's
easily scriptable using your favorite shell:

.. code-block:: text

    $ tomcat-manager --user=ace --password=newenglandclamchowder \
    http://localhost:8080/manager deploy local sample.war /sampleapp
    $ echo $?
    0

There is also an interactive mode:

.. code-block:: text

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
    >>> r = tomcat.connect(url="http://localhost:8080/manager",
    ... user="ace", password="newenglandclamchowder")
    >>> tomcat.is_connected
    True
    >>> r = tomcat.stop("/someapp")
    >>> r.status_code == tm.StatusCode.OK
    False
    >>> r.status_message
    'No context exists named /someapp'

The following capabilites are supported from :doc:`interactive use
<interactive/tomcatmanager>`, the :doc:`commandline`, and from :doc:`python
<api/index>`:

    - **deploy** - deploy a war file containing a tomcat application in the tomcat
      server
    - **redeploy** - remove the application currently installed at a given path and
      install a new war file there
    - **undeploy** - remove an application from the tomcat server
    - **start** - start a tomcat application that has been deployed but isn't running
    - **stop** - stop a tomcat application and leave it deployed on the server
    - **reload** - stop and start a tomcat application
    - **sessions** - show active sessions for a particular tomcat application
    - **expire** - expire idle sessions
    - **list** - show all installed applications
    - **serverinfo** - show information about the server, including tomcat version, OS
      version and architecture, and jvm version
    - **status** - show server status information in xml format
    - **vminfo** - show diagnostic information about the jvm
    - **threaddump** - show a jvm thread dump
    - **resources** - show the global jdni resources configured in tomcat
    - **findleakers** - show tomcat applications that leak memory
    - **sslconnectorciphers** - show tls ciphers configured for each connector
    - **sslconnectorcerts** - show tls certificate chain for each virtual host
    - **sslconnectortrustedcerts** - show trusted certificates for each virtual host
    - **sslreload** - reload tls certificate and key files


Table of Contents
-----------------

.. toctree::
    :maxdepth: 2

    install
    configuretomcat
    interactive/index.rst
    commandline
    package
    authentication
    api/index.rst
    contributing
    changelog
