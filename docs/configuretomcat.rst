Configure Tomcat
================

This library and associated tools do their work via the `Tomcat Manager
<https://tomcat.apache.org/tomcat-8.5-doc/manager-howto.html>`_ web application
included in the Tomcat distribution.

You will need the url where the Tomcat Manager application is available. You
can use the URL that points directly to the container, or the URL of a proxy
like nginx or Apache HTTP Server you have deployed in front of Tomcat. TLS is
recommended, but it works without if you must.

You will also need to configure authentication for a user, and grant that user
permission to access the Tomcat Manager application. The full details of this
procedure can be found in the `Tomcat Manager Howto
<https://tomcat.apache.org/tomcat-8.5-doc/manager-howto.html#Configuring_Manager
_Application_Access>`_. A short summary is included here.

You will need to configure authentication in ``tomcat-users.xml`` with access
to the ``manager-script`` role. The username and password can be anything of
your choosing. Here's how to configure the user we will use as an example
throughout the tomcatmanager documentation:

.. code-block:: xml

  <tomcat-users>
    ...
    <role rolename="manager-script"/>
    <user username="ace" password="newenglandclamchowder" roles="manager-script"/>
    ...
  </tomcat-users>
