Migrating to version 3.x
========================

Version 3 of tomcatmanager adds several new capabilities, and makes a few
breaking changes. See the :doc:`/changelog` for a short summary. This document
explains the reasoning behind the changes and includes specific guidance for
migrating from version 2.

Version 3 contains two new capabilities. First, additional SSL/TLS server certificate
verification options and client authentication options have been added. These new
capabilities are described in :doc:`/authentication` and are implemented in a
completely backwards compatible way. Pass additional keyword-only parameters to the
:meth:`.TomcatManager.connect()` method to access these features.

Second, not all supported versions Tomcat (and the Manager application included in the
distribution), implement the same set of manager commands. For example, the `sslReload
<http://tomcat.apache.org/tomcat-10.0-doc/manager-howto.html#Reload_TLS_configuration>`_
command is implemented in Tomcat 10.x, but not in Tomcat 7.x. If you called the
:meth:`.TomcatManager.ssl_reload()` method after connecting to a Tomcat 7.x server, an
exception was raised, but it was a HTTP error and you couldn't really tell that the
problem was that this command wasn't implemented by that server. Exposing a reliable
mechanism to raise new exceptions in this scenario required some breaking changes.

HTTP is a stateless protocol. Web developers have come up with various strategies for
preserving state across multiple requests, including session tokens and cookies.
Tomcatmanager 2.x had no reason to preserve state across multiple calls to the server.
When you called the :meth:`.TomcatManager.connect()` method it made a HTTP request to
the ``url`` attribute, and created a HTTP Basic authentication header using the
contents of the ``user`` attribute. Because there was no state, you could freely
modify either of those attributes at any time, and the HTTP request would throw
exceptions if errors occured.

In tomcatmanager 3.x we need to know what version of the server is on the other end of
the line. We could either have a super-chatty network exchange and query the server
before every request to figure out what version it is, or we can figure it on our
first request, and then preserve the state across all of our other requests. I chose
the latter.

This means that the original philosophy for connect needed to be modified. In
tomcatmanager 2.x you could change the url it didn't matter. In tomcatmanager 3.x if
you change the url or the user, our preserved state needs to be invalidated. To
accommodate this change in approach, some breaking changes were made to the API in
tomcatmanager 3.x:

- :attr:`.TomcatManager.user` is now a read-only property instead of a read-write
  attribute, use :meth:`.TomcatManager.connect()` to set this value.
- :attr:`.TomcatManager.url` is now a read-only property instead of a read-write
  attribute, use :meth:`.TomcatManager.connect()` to set this value
- if you call a method on :class:`.TomcatManager` which requires network interaction
  with the Tomcat server (which is all the methods that do anything interesting) and
  you haven't called :meth:`.TomcatManager.connect()` first,
  :exc:`.TomcatNotConnected` will be raised. In tomcatmanager 2.x, you will either
  connect successfully if you had set :attr:`.TomcatManager.url` properly, or you
  would get some sort of HTTP error.
- since we were already making a breaking change to :meth:`.TomcatManager.connect()`,
  I decided to make another: the ``timeout`` parameter used to be positional, now it
  is keyword only. If you were passing it as positional, your calls to
  :meth:`.TomcatManager.connect()` will now break, and you'll have to fix them. If you
  were specifying the timeout by setting the :attr:`.TomcatManager.timeout` attribute,
  that continues to work as before.

If you are assigning values to :attr:`.TomcatManager.user` or
:attr:`.TomcatManager.url`, I've got bad news, your code will break badly. The good
news is that these should be easy to find and fix. You'll have to pass these
parameters to the :meth:`.TomcatManager.connect()` method now.

That's it for migrating. There are a bunch of new features in tomcatmanager 3.x which
you can take advantage of (see the :doc:`/changelog`), but none of them will break
your existing code.
