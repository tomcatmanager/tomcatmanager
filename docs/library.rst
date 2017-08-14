Using TomcatManager from Python
===============================

Overview
--------

.. autoclass:: tomcatmanager.TomcatManager


Connect to the server
---------------------

Before you can do anything useful, you need to create a
:class:`TomcatManager <tm.TomcatManager>` object
and tell it how to connect to the server.

.. automethod:: tomcatmanager.TomcatManager.__init__

Alternatively, you can use the :meth:`connect()
<tomcatmanager.tomcat_manager.TomcatManager.connect>` method, which unlike
creating the object, actually tries to connect to the server.

.. automethod:: tomcatmanager.TomcatManager.connect


Responses from the server
-------------------------

.. autoclass:: tomcatmanager.models.TomcatManagerResponse
   :members:

Deploying applications
----------------------

.. automethod:: tomcatmanager.TomcatManager.deploy

You can also undeploy applications. This removes the WAR file from the Tomcat server.

.. automethod:: tomcatmanager.TomcatManager.undeploy


Other application commands
--------------------------

.. automethod:: tomcatmanager.TomcatManager.list

.. automethod:: tomcatmanager.TomcatManager.start

.. automethod:: tomcatmanager.TomcatManager.stop

.. automethod:: tomcatmanager.TomcatManager.reload

.. automethod:: tomcatmanager.TomcatManager.sessions

.. automethod:: tomcatmanager.TomcatManager.expire

Parallel Deployments
--------------------

Tomcat supports a `parallel deployment feature <https://tomcat.apache.org/tomcat-8.0-doc/config/context.html#Parallel_deployment>`_ which allows multiple versions of the same WAR to be deployed simultaneously at the same URL. To utilize this feature, you need to deploy an application with a version string. The combination of path and version string uniquely identify the application.



The following methods include an optional version parameter to support parallel deployments:

- :meth:`deploy`
- :meth:`undeploy`
- :meth:`start`
- :meth:`stop`
- :meth:`reload`
- :meth:`sessions`
- :meth:`expire`


Information about Tomcat
------------------------

.. automethod:: tomcatmanager.TomcatManager.server_info

.. automethod:: tomcatmanager.TomcatManager.status_xml

.. automethod:: tomcatmanager.TomcatManager.vm_info

.. automethod:: tomcatmanager.TomcatManager.ssl_connector_ciphers

.. automethod:: tomcatmanager.TomcatManager.thread_dump

.. automethod:: tomcatmanager.TomcatManager.resources

.. automethod:: tomcatmanager.TomcatManager.find_leakers



