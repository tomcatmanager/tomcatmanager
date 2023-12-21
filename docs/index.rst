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

.. image:: demos/interactive-tour.gif
    :alt: demo of tomcat-manager interactive mode

And for the ultimate in flexibility, you can use the python package directly:

.. image:: demos/package.gif
    :alt: demo of tomat-manager python package

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
