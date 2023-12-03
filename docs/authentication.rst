Authentication
==============

There are several methods available to ensure secure communication and
authentication between tomcatmanager and a Tomcat server.


Encrypted Connections
---------------------

For anything other than local development use, you should ensure that all communications
with your Tomcat server are secured with SSL/TLS. Tomcat has `extensive SSL/TLS
configuration documentation
<https://tomcat.apache.org/tomcat-10.0-doc/ssl-howto.html>`_. You can also configure a
proxy to terminate SSL/TLS and pass the unencrypted traffic to Tomcat.

* `Apache httpd as proxy for Tomcat
  <https://tomcat.apache.org/tomcat-10.0-doc/proxy-howto.html>`_
* `NGINX as a load-balanced proxy for Tomcat
  <https://docs.nginx.com/nginx/deployment-guides/load-balance-third-party/apache-tomcat/>`_.

To use these encrypted connections with tomcatmanager, simply use the ``https``
protocol in the url you specify for the server. The ``list`` command shown here can be
replaced with any supported command. Here are examples from the command line,

.. code-block:: text

    $ tomcat-manager --user=ace --password=newenglandclamchowder \
    https://www.example.com/manager list

interactive mode,

.. code-block:: text

    $ tomcat-manager
    tomcat-manager>connect https://www.example.com/manager ace newenglandclamchowder
    --connected to https://www.example.com/manager as ace


and from Python:

.. code-block:: python

    url = 'https://www.example.com/manager'
    user = 'ace'
    password = 'newenglandclamchowder'
    tomcat = tm.TomcatManager()
    r = tomcat.connect(url, user, password)

Tomcatmanager uses the `requests
<https://requests.readthedocs.io/en/latest/>`_ library for network
communication. A SSL/TLS certificate presented by the server will be rejected if not
signed by one of the certificate authorities included in `requests
<https://requests.readthedocs.io/en/latest/>`_.

Installing the `certifi <https://github.com/certifi/python-certifi>`_ python package
will cause `requests <https://requests.readthedocs.io/en/latest/>`_ to use
Mozilla's carefully curated collection of root certificates instead of the built-in
ones. Highly recommended.

Server certificates from most commercial certificate authorities will just work.
So will the free certificates issued by `Lets Encrypt <https://letsencrypt.org/>`_.


Using your own certificate authority
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can use your own certificate authority with a root certificate not cross-signed
by one of the well known certificate authorities. You'll need the path to your
certificate authority bundle file, or the path to a directory containing
certificates of trusted certificate authorities.

.. note::

    If you use a directory, you must process the files in that directory using
    the `c_rehash <https://www.openssl.org/docs/man1.1.0/man1/c_rehash.html>`_
    tool supplied with OpenSSL.

Use the ``--cacert`` option from the command line. The ``list`` command shown here can
be replaced with any supported command.

.. code-block:: text

    $ tomcat-manager --user=ace --password=newenglandclamchowder \
    --cacert=/etc/ssl/mycertbundle https://www.example.com/manager list

Interactive mode is similar:

.. code-block:: text

    $ tomcat-manager
    tomcat-manager>connect --cacert=/etc/ssl/mycertbundle https://www.example.com/manager ace newenglandclamchowder
    --connected to https://www.example.com/manager as ace

From Python use the :attr:`~.TomcatManager.verify` parameter to the
:meth:`.TomcatManager.connect` method:

.. code-block:: python

    url = "https://www.example.com/manager"
    user = "ace"
    password = "newenglandclamchowder"
    cacert = "/etc/ssl/mycertbundle"
    tomcat = tm.TomcatManager()
    r = tomcat.connect(url, user, password, verify=cacert)


Disabling certificate verification
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can disable client verification of server SSL/TLS certificates. While useful in
some development or testing scenarios, you should not do this when connecting to a
production server.

.. warning::

    With client verification disabled, a malicious actor can intercept
    communications from the client to the server without the user knowing.

Use the ``--noverify`` option from the command line:

.. code-block:: text

    $ tomcat-manager --user=ace --password=newenglandclamchowder \
    --noverify https://www.example.com/manager list

from interactive mode:

.. code-block:: text

    $ tomcat-manager
    tomcat-manager>connect --noverify https://www.example.com/manager ace newenglandclamchowder
    --connected to https://www.example.com/manager as ace

or pass ``False`` in the :attr:`~.TomcatManager.verify` parameter of the
:meth:`.TomcatManager.connect` method:

.. code-block:: python

    url = "https://www.example.com/manager"
    user = "ace"
    password = "newenglandclamchowder"
    tomcat = tm.TomcatManager()
    r = tomcat.connect(url, user, password, verify=False)


HTTP Basic Authentication
-------------------------

All the examples in the tomcatmanager documentation demonstrate using a username and
password to authenticate with the Tomcat server. This uses HTTP Basic Authentication
which presents those credentials in the ``Authorization`` header of every HTTP request
sent to the server.

This method is supported out of the box in the default configuration of Tomcat
servers. When you add users and passwords to ``tomcat-users.xml`` you can authenticate
as shown in any example in this documentation.

.. warning::

    HTTP Basic Authentication is not secure when used over an unencrypted connection.


SSL/TLS Client Authentication
-----------------------------

We've discussed how clients can verify servers using SSL/TLS, but what if a server
want's to verify a client? Servers configured with `SSL/TLS Client Authentication
<https://aboutssl.org/ssl-tls-client-authentication-how-does-it-works/>`_ use public
key authentication to validate a certificate installed on the client.

As best I can tell, current versions of Tomcat do not support client authentication. I
also can't seem to find a way to use the Common Name of a client certificate as an
authenticated user in Tomcat. If you know how to configure this on a Tomcat server, or
find some current documentation showing how to do so, please `create a new issue
<https://github.com/tomcatmanager/tomcatmanager/issues/new>`_ on github and I'll add
it here.

Assuming you have that all figured out, here's how you do the client side part using
tomcatmanager. I've excluded the user and password from these examples. However, it
is possible to have a configuration that does both SSL/TLS client authentication and
HTTP Basic authentication using a user and password. If you are issuing the keys and
certificates from a private certificate authority, you will need to combine the methods
above for doing so with the options shown here.

Client authentication uses public key cryptography, where you have a private key that
you never share with anyone, and a public key (or certificate in SSL/TLS lingo) that
can be freely shared. You can have your key and your certificate in separate files,
or they can be combined into a single file.

.. warning::

    When creating a private key you can protect it with a passphrase, which encrypts
    the private key. To use the key you must enter the passphrase. In order to work
    with tomcatmanager, the private key for your local certificate must be unencrypted.
    The Requests library used for network communication does not support using
    encrypted keys.

Use the ``--key`` and ``--cert`` options from the command line to specify the private
key and associated certificate used to respond to the authentication requests from the
server. If you have the key and the certificate in a single file, then omit the
``--key`` option and use the combined file with the ``--cert`` option:

.. code-block:: text

    $ tomcat-manager --key /etc/ssl/mykey --cert /etc/ssl/mycert \
    https://www.example.com/manager list

Interactive mode works simiarly, this example shows how to use a combined key and
certificate file:

.. code-block:: text

    $ tomcat-manager
    tomcat-manager>connect --cert /etc/ssl/mycertandkey https://www.example.com/manager
    --connected to https://www.example.com/manager authenticated by /etc/ssl/mycertandkey

The :meth:`.TomcatManager.connect` method accepts a ``cert`` keyword-only parameter.
If your key and certificate are in the same file, pass the filename in that parameter.
If they are in separate files, pass a tuple with the cert and the key:

.. code-block:: python

    url = "https://www.example.com/manager"
    user = "ace"
    password = "newenglandclamchowder"
    certandkey = ("/etc/ssl/mycert", "/etc/ssl/mykey")
    tomcat = tm.TomcatManager()
    r = tomcat.connect(url, user, password, cert=certandkey)
