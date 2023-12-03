tomcatmanager
=============

.. image:: https://img.shields.io/pypi/v/tomcatmanager?label=latest%20version
      :target: https://pypi.python.org/pypi/tomcatmanager
      :alt: latest version
.. image:: https://img.shields.io/pypi/pyversions/tomcatmanager
      :target: https://pypi.python.org/pypi/tomcatmanager
      :alt: supported python versions
.. image:: https://img.shields.io/badge/license-MIT-orange
      :target: https://github.com/tomcatmanager/tomcatmanager/blob/main/LICENSE
      :alt: license
.. image:: https://img.shields.io/github/actions/workflow/status/tomcatmanager/tomcatmanager/quicktest.yml?branch=main&label=build%20%28main%29
      :target: https://github.com/tomcatmanager/tomcatmanager/tree/main
      :alt: main branch build status
.. image:: https://img.shields.io/github/actions/workflow/status/tomcatmanager/tomcatmanager/quicktest.yml?branch=develop&label=build%20%28develop%29
      :target: https://github.com/tomcatmanager/tomcatmanager/tree/develop
      :alt: develop branch build status
.. image:: https://img.shields.io/codecov/c/github/tomcatmanager/tomcatmanager/main?token=3YbxJ1PKwJ
      :target: https://codecov.io/gh/tomcatmanager/tomcatmanager
      :alt: code coverage
.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
      :target: https://github.com/astral-sh/ruff
      :alt: Ruff
.. image:: https://img.shields.io/badge/code%20style-black-000000
      :target: https://github.com/psf/black
      :alt: code style black
.. image:: https://img.shields.io/github/actions/workflow/status/tomcatmanager/tomcatmanager/doctest.yml?branch=main&label=docs%20%28main%29
      :target: http://tomcatmanager.readthedocs.io/en/stable
      :alt: main branch documentation status
.. image:: https://img.shields.io/github/actions/workflow/status/tomcatmanager/tomcatmanager/doctest.yml?branch=main&label=docs%20%28develop%29
      :target: https://tomcatmanager.readthedocs.io/en/develop/
      :alt: develop branch documentation status


If you use Apache Tomcat for any sort of development work you’ve probably deployed
lots of applications to it. There are a several ways to get your war files deployed:

- use the `Tomcat Manager <https://tomcat.apache.org/tomcat-9.0-doc/manager-howto.html>`_
  application in your browser
- use the `Tomcat Ant Tasks <https://cwiki.apache.org/confluence/display/tomcat/AntDeploy>`_ included with
  Tomcat
- use `Cargo <https://codehaus-cargo.github.io/>`_ and its plugins for ant and maven

Here's another way: a command line tool and python library for managing a Tomcat server.


How Do I Use It?
----------------

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
   tomcat-manager>connect http://localhost:8080/manager ace
   Password:
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
   >>> r.ok
   False
   >>> r.status_message
   'No context exists named /someapp'


What Can It Do?
---------------

Tomcatmanager has the following capabilities, all available from the command line,
interactive mode, and as a python library:

- **deploy** - deploy a war file containing a tomcat application in the tomcat server
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


Documentation
-------------

Complete documentation for the last released version is available at
`<http://tomcatmanager.readthedocs.io/en/stable/>`_. It includes material
showing how to use ``tomcat-manager`` from the command line or using
interactive mode. There is also a walkthrough of how to use the API and an
API reference.

Documentation is also built from the `develop
<https://github.com/tomcatmanager/tomcatmanager/tree/develop>`_ branch, and
published at `<https://tomcatmanager.readthedocs.io/en/latest/>`_. The develop
branch may not yet be released to PyPi, but you can see the documentation for what's
coming up in the next release.


Installation
------------

You'll need Python >= 3.8. Install using pip:

.. code-block:: text

   $ pip install tomcatmanager

Works on Windows, macOS, and Linux.

Works with Tomcat >= 8.5 and <= 10.1.


Tomcat Configuration
--------------------

This library and associated tools do their work via the Tomcat Manager
web application included in the Tomcat distribution. You will need to
configure authentication in ``tomcat-users.xml`` with access to the
``manager-script`` role:

.. code-block:: xml

   <tomcat-users>
     ...
     <role rolename="manager-script"/>
     <user username="ace" password="newenglandclamchowder" roles="manager-script"/>
     ...
   </tomcat-users>

