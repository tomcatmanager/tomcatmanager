Connect and Deploy
==================

Connect To A Tomcat Server
--------------------------

Before you can do anything to a Tomcat server, you need to enter the connection
information, including the url and the authentication credentials. You can pass
the connection information on the command line:

.. code-block:: text

    $ tomcat-manager --user=ace http://localhost:8080/manager
    Password: {you type your password here}

Or:

.. code-block:: text

    $ tomcat-manager --user=ace --password=newenglandclamchowder \
    http://localhost:8080/manager

You can also enter this information into the interactive prompt:

.. code-block:: text

    $ tomcat-manager
    tomcat-manager> connect http://localhost:8080/manager ace newenglandclamchowder

Or:

.. code-block:: text

    $ tomcat-manager
    tomcat-manager> connect http://localhost:8080/manager ace
    Password: {type your password here}

See :doc:`/authentication` for complete details on all supported authentication
mechanisms.


Deploy applications
-------------------

Tomcat applications are usually packaged as a WAR file, which is really just a
zip file with a different extension. The ``deploy`` command sends a WAR file to
the Tomcat server and tells it which URL to deploy that application at.

The WAR file can be located in one of two places: some path on the computer
that is running Tomcat, or some path on the computer where the command line
``tomcat-manager`` program is running.

If the WAR file is located on the same server as Tomcat, we call that
``server``. If the WAR file is located where ``tomcat-manager`` is running, we
call that ``local``. If the file is already on the server, then we have to tell
Tomcat where to go find it. If it's ``local``, then we have to send the WAR
file over the network so Tomcat can deploy it.

For all of these examples, lets assume I have a Tomcat server running far away
in a data center somewhere, accessible at ``https://www.example.com``. I'm
running the command line ``tomcat-manager`` program on my laptop. We'll also
assume that we have already connected to the Tomcat server, using one of the
methods just described in :ref:`interactive/connectdeploy:Connect To A Tomcat Server`.

For our first example, let's assume we have a WAR file already on our server,
in ``/tmp/fancyapp.war``. To deploy this WAR file to
``https://www.example.com/fancy``:

.. code-block:: text

    tomcat-manager> deploy server /tmp/myfancyapp.war /fancy

Now let's say I just compiled a WAR file on my laptop for an app called
``shiny``. It's saved at ``~/src/shiny/dist/shinyv2.0.5.war``. I'd like to
deploy it to ``https://www.example.com/shiny``:

.. code-block:: text

    tomcat-manager> deploy local ~/src/shiny/dist/shiny2.0.5.war /shiny

Sometimes when you deploy a WAR you want to specify additional configuration
information. You can do so by using a `context file
<https://tomcat.apache.org/tomcat-8.5-doc/config/context.html>`_. The context
file must reside on the same server where Tomcat is running.

.. code-block:: text

    tomcat-manager> deploy context /tmp/context.xml /sample

This command will deploy the WAR file specified in the ``docBase`` attribute of
the ``Context`` element so it's available at
``https://www.example.com/sample``.

.. note::

    When deploying via context files, be aware of the following:

    - The ``path`` attribute of the ``Context`` element is ignored by the Tomcat
      Server when deploying from a context file.

    - If the ``Context`` element specifies a ``docBase`` attribute, it will be
      used even if you specify a war file on the command line.


Parallel Deployment
-------------------

Tomcat supports a `parallel deployment feature
<https://tomcat.apache.org/tomcat-10.1-doc/config/context.html#Parallel_deplo
yment>`_ which allows multiple versions of the same WAR to be deployed
simultaneously at the same URL. To utilize this feature, you need to deploy
an application with a version string. The combination of path and version
string uniquely identify the application.

Let's revisit our ``shiny`` app. This time we will deploy with a version
string:

.. code-block:: text

    tomcat-manager> deploy local ~/src/shiny/dist/shiny2.0.5.war /shiny -v v2.0.5
    tomcat-manager> list
    Path                     Status  Sessions Directory
    ------------------------ ------- -------- ------------------------------------
    /                        running        0 ROOT
    /manager                 running        0 manager
    /shiny                   running        0 shiny##v2.0.5

Later today, I make a bug fix to 'shiny', and build version 2.0.6 of the app. Parallel
deployment allows me to deploy two versions of that app at the same path, and Tomcat
will migrate users to the new version over time as their sessions expire in version
2.0.5.

.. code-block:: text

    tomcat-manager> deploy local ~/src/shiny/dist/shiny2.0.6.war /shiny -v v2.0.6
    tomcat-manager> list
    Path                     Status  Sessions Directory
    ------------------------ ------- -------- ------------------------------------
    /                        running        0 ROOT
    /manager                 running        0 manager
    /shiny                   running       12 shiny##v2.0.5
    /shiny                   running        0 shiny##v2.0.6

Once all the sessions have been migrated to version 2.0.6, I can undeploy
version 2.0.5:

.. code-block:: text

    tomcat-manager> undeploy /shiny --version v2.0.5
    tomcat-manager> list
    Path                     Status  Sessions Directory
    ------------------------ ------- -------- ------------------------------------
    /                        running        0 ROOT
    /manager                 running        0 manager
    /shiny.                  running        9 shiny##v2.0.6

The following commands support the ``-v`` or ``--version`` option, which makes
parallel deployment possible:

- deploy
- undeploy
- start
- stop
- reload
- sessions
- expire
