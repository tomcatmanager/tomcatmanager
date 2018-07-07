Configure Tomcat
================

Supported Tomcat Versions
-------------------------

The following Tomcat versions are supported:

- 7.0.x
- 8.0.x
- 8.5.x
- 9.0.x

The operating system and Java Virtual Machine don't matter as long as Tomcat
runs on it.

Authentication
--------------

This library and associated tools do their work via the `Tomcat Manager
<https://tomcat.apache.org/tomcat-9.0-doc/manager-howto.html>`_ web application
included in the Tomcat distribution.

You will need the URL where the Tomcat Manager application is available. You
can use the URL that points directly to the container, or the URL of a proxy
like nginx or Apache HTTP Server you have deployed in front of Tomcat. TLS is
recommended, but it works without if you must.

You will also need to configure authentication for a user, and grant that user
permission to access the Tomcat Manager application. The full details of this
procedure can be found in the `Tomcat Manager Howto
<https://tomcat.apache.org/tomcat-9.0-doc/manager-howto.html#Configuring_Manager
_Application_Access>`_. A short summary is included here.

Configure a user in ``tomcat-users.xml`` and grant that user the
``manager-script`` role. The username and password can be anything of your
choosing. Here's how to configure the user we will use as an example throughout
this documentation:

.. code-block:: xml

  <tomcat-users>
    ...
    <role rolename="manager-script"/>
    <user username="ace" password="newenglandclamchowder" roles="manager-script"/>
    ...
  </tomcat-users>
