Configuration File
==================

``tomcat-manager`` reads a user configuration file on startup. This file allows
you to:

- change settings on startup
- create Tomcat server definitions that include the url and authentication credentials

The ```--noconfig`` command line option prevents ``tomcat-manager`` from
processing the configuration file on startup.


Location
--------

The location of the configuration file is different depending on your operating
system. To see the location of the file on your system, run the following
command from within ``tomcat-manager``:

.. code-block:: text

    tomcat-manager> config file
    /Users/kotfu/Library/Application Support/tomcat-manager/tomcat-manager.toml

Editing
-------

You can edit the file from within ``tomcat-manager`` too. Well, it really just
launches the editor of your choice, you know, the one specified in the
:ref:`interactive/settings:editor` setting . Do that by typing:

.. code-block:: text

    tomcat-manager> config edit

Syntax
------

The configuration file uses the `TOML <https://toml.io/>`_ file format. `TOML
<https://toml.io/>`_ is a simple configuration file format that's easy for humans to
read. ``tomcat-manager`` doesn't have complex configuration requirements, so `TOML
<https://toml.io/>`_ is a great fit. Here's an example configuration file in TOML
format:

.. code-block:: toml

    [settings]
    prompt = "tm> "
    debug = true
    editor = "/usr/bin/mg"
    echo = false
    quiet = false
    status_prefix = "--"

    [tcl]
    url = "http://localhost:8080/manager"
    user = "ace"
    password = "newenglandclamchowder"

.. note::

    In versions prior to 6.0.0, the configuration file used the Microsoft Windows INI
    file format, which is similar to TOML. For the ``tomcat-manager`` configuration
    file, the biggest difference between these two formats is that all string values
    must be quoted in TOML, and in INI they are accepted without quotes.

    When you run ``tomcat-manager`` in interactive mode it will check if the old
    configuration file is present. If it is, and if the new configuration file doesn't
    exist, it will let you know.

    .. code-block:: text

        $ tomcat-manager
        --In version 6.0.0 the configuration file format changed from INI to TOML.
        --You have a configuration file in the old format. Type 'config convert' to
        --migrate your old configuration to the new format.

    Convert your configuration file to the new format:

    .. code-block:: text

        tomcat-manager> config convert
        --converting old configuration file to new format
        --configuration written to /Users/kotfu/Library/Application Support/tomcat-manager/tomcat-manager.toml
        --reloading configuration

    Everything is converted to the new format automatically except comments. You'll have
    to add your comments back in by hand.

Settings
--------

Create a table called ``settings``, and use key/value pairs to set values for any of
the available settings. These settings are applied when ``tomcat-manager`` starts,
and applied again after you finish editing the config file. Here's an example of
settings in the config file:

.. code-block:: toml

    [settings]
    prompt = "tm> "
    debug = true
    editor = "/usr/bin/mg"
    echo = false
    quiet = false
    status_prefix = "--"

See :ref:`interactive/settings:Settings` for documentation on every setting.


Server Definitions
------------------

In addition to settings, you can use the configuration file to define Tomcat servers.
The definition includes a name, the url, and authentication credentials. Create server
definitions in your configuration file to keep the the authentication credentials off
of the command line and out of your scripts, which is more secure.

A server definition is contained in a TOML table. The name of the table is the name of
the server, and the various items in the table contain the details about that server.
Here's a simple example:

.. code-block:: toml

    [local]
    url = "http://localhost:8080/manager"
    user = "ace"
    password = "newenglandclamchowder"

With this defined in your configuration file, you can now connect using the name of
the server:

.. code-block:: text

    tomcat-manager> connect local

You can also use the server name from the command line instead of providing the url:

.. code-block:: text

    $ tomcat-manager local

If you define a ``user``, but omit ``password``, you will be prompted for it
when you use the server definition in the ``connect`` command.

Here's all the properties supported in a server definition:

url
    Url of the server.

user
    User to use for HTTP Basic authentication.

password
    Password to use for HTTP Basic authentication. If user is provided
    and password is not, you will be prompted for a password.

cert
    File containing certificate and key, or just a certificate, for SSL/TLS client
    authentication. See :ref:`authentication:SSL/TLS Client Authentication` for more
    information.

key
    File containing private key for SSL/TLS client authentication. See
    :ref:`authentication:SSL/TLS Client Authentication` for more information.

cacert
    File or directory containing a certificate authority bundle used to validate the
    SSL/TLS certificate presented by the server if the url uses the https protocol. See
    :ref:`authentication:Encrypted Connections` for more information.

verify
    Defaults to ``True`` to verify server SSL/TLS certificates. If ``False``,
    no verification is performed.

When using a server definition, you can override properties from the definition
on the command line. For example, if we had a server defined like this:

.. code-block:: toml

    [prod]
    url = "https://www.example.com/manager"
    user = "ace"
    password = "newenglandclamchowder"
    cacert = "/etc/mycacert"

You could use that server definition but temporarily disable verification of server
SSL/TLS certificates:

.. code-block:: text

    tomcat-manager> connect prod --noverify

Or you could override the user and password:

.. code-block:: text

    tomcat-manager> connect prod root Z1ON0101

Some of these properties make no sense when combined together. For example, if your
server authenticates with a certificate and key, it almost certainly doesn't use a
user and password. If you don't want to verify server SSL/TLS certificates, then it
makes no sense to provide a certificate authority bundle. See
:ref:`authentication:Authentication` for complete details of all supported
authentication mechanisms.
