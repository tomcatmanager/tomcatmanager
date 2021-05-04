#
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007 Jared Crapo
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# pylint: disable=too-many-lines
"""
tomcatmanager
-------------

A python wrapper for interacting with the Tomcat Manager web application.
"""

import functools
import collections
import re
from typing import Any, Callable, List, Tuple, Union

import requests

from .models import (
    TomcatManagerResponse,
    StatusCode,
    ServerInfo,
    TomcatApplication,
    TomcatMajorMinor,
    TomcatNotImplementedError,
    TomcatNotConnected,
)

# pylint: disable=too-many-public-methods
class TomcatManager:
    """
    A class for interacting with the Tomcat Manager web application.


    Here's a summary of the recommended way to use this class with proper
    exception and error handling. For this example, we'll use the
    `server_info()` method.

    .. code-block:: python

       import tomcatmanager as tm
       url = "http://localhost:808099/manager"
       user = "ace"
       password = "newenglandclamchowder"
       tomcat = tm.TomcatManager()
       try:
           r = tomcat.connect(url, user, password)
           if r.ok:
               r = tomcat.server_info()
               if r.ok:
                   print(r.server_info)
               else:
                   print("Error: {}".format(r.status_message))
           else:
               print("not connected")
       except Exception as err:
           # handle exception
           print("not connected")
    """

    class _implemented_by:
        """Decorator to show which versions of tomcat implement this method.

        Most methods in TomcatManager work in all versions of Tomcat, and we
        expect they will work in future versions of Tomcat too. Use the
        decorator like this:

            @_implemented_by(TomcatMajorMinor.supported() + [TomcatMajorMinor.VNEXT])
            def list(self):
                ...

        If a method is known to only work in certain versions of Tomcat, use
        the decorator like this:

            @_implemented_by(
                [
                    TomcatMajorMinor.V8_5,
                    TomcatMajorMinor.V9_0,
                    TomcatMajorMinor.V10_0,
                    TomcatMajorMinor.VNEXT,
                ]
            )
            def ssl_reload(self):
                ...

        """

        # pylint: disable=invalid-name, too-few-public-methods

        matrix = {}

        def __init__(self, tomcats):
            # self is the instance of _implemented_by
            # these are the arguments passed to the decorator
            # we assume tomcats is a list
            self.tomcats = tomcats

        def __call__(self, method):
            # this ensures that the wrapper has the dunder attributes
            # of the method we are wrapping
            self.matrix[method.__name__] = self.tomcats

            @functools.wraps(method)
            def wrapper(celff, *args, **kwargs):
                # this is the function wrapper around the decorated method
                # celff is the instance of TomcatManager
                # these are the arguments passed to the decorated function
                if celff.is_connected:
                    if celff.tomcat_major_minor in self.tomcats:
                        return method(celff, *args, **kwargs)
                    raise TomcatNotImplementedError(
                        "'{}' not implemented on Tomcat {}".format(
                            method.__name__, celff.tomcat_major_minor.value
                        )
                    )
                raise TomcatNotConnected("not connected")

            return wrapper

    def __init__(self):
        """
        Initialize a new TomcatManager object.
        """
        self._url = None
        self._user = None

        # ask nicely for people not to access the password attribute
        self._password = None

        # same with the certificates for client side authentication
        self._cert = None

        # and the CA bundle to verify server SSL/TLS certifications,
        # or False to skip verification
        self._verify = None

        # where we keep track of the version of tomcat we are connected to
        # this is set by connect()
        self._tomcat_major_minor = None

        self.timeout = 10.0
        """Seconds to wait before giving up on network operations. Can be a
        ``float`` or an ``int``. Default is ``10``. I surely don't want to wait forever,
        but if you do, set to ``0``.

        Usage::

        >>> import tomcatmanager as tm
        >>> tomcat = tm.TomcatManager()
        >>> tomcat.timeout = 3.5

        .. versionchanged:: 3.0.0
           Can be a ``float`` or ``int`` instead of just an ``int``
        """

    @property
    def url(self) -> str:
        """Url of the Tomcat Manager web application we are connected to.

        This attribute is set by the :meth:`.connect` method. Look there for
        more info.

        .. versionchanged:: 3.0.0
           Now a read-only property instead of a read-write attribute.
        """
        return self._url

    @property
    def user(self) -> str:
        """User we successfully authenticated to the Tomcat Manager web
        application with.

        This attribute is set by the :meth:`.connect` method. Look there for
        more info.

        .. versionchanged:: 3.0.0
           Now a read-only property instead of a read-write attribute.
        """
        return self._user

    @property
    def cert(self) -> Union[str, Tuple[str, str]]:
        """Client side SSL/TLS certificates we authenticated to the Tomcat Manager
        web application with.

        This attribute is set by the :meth:`.connect` method. Look there for
        more info.

        .. versionadded:: 3.0.0
        """
        return self._cert

    @property
    def verify(self) -> Union[str, bool]:
        """The certificate authority directory or bundle to use to verify
        server SSL/TLS certificates. If ``False`` no verification is performed.

        This attribute is set by the :meth:`.connect` method. Look there for more info.

        .. versionadded:: 3.0.0
        """
        return self._verify

    @property
    def tomcat_major_minor(self) -> TomcatMajorMinor:
        """If connected to a server, this contains an instance of
        :class:`.TomcatMajorMinor` describing the major version of
        Tomcat we are connected to.

        This attribute is set by the :meth:`.connect` method. Look there for more info.

        .. versionadded:: 3.0.0
        """
        return self._tomcat_major_minor

    def implements(self, method: Union[Callable, str]) -> bool:
        """Is a method implemented on the tomcat server we are connected to?

        :param method:      a method on :class:`.TomcatManager` to check if is
                            implemented
        :return:            ``True`` if the method is implemented, ``False`` otherwise
        :raises TomcatNotConnected: if we are not currently connected to a tomcat server

        Not all versions of Tomcat implement all of the methods of
        :class:`.TomcatManager`. Use this to check whether a method on this class
        is implemented by the version of the Tomcat server we are connected to.
        The method parameter accepts a string containing the method name or the
        method itself.

        Usage:

        .. code-block:: python

           import tomcatmanager as tm
           tomcat = tm.TomcatManager()
           tomcat.connect("http://localhost:8080", "ace", "newenglandclamchowder")
           print(tomcat.implements(tomcat.deploy_localwar))

        or:

        .. code-block:: python

           import tomcatmanager as tm
           tomcat = tm.TomcatManager()
           tomcat.connect("http://localhost:8080", "ace", "newenglandclamchowder")
           print(tomcat.implements(tomcat.deploy_localwar))

        .. versionadded:: 3.0.0
        """
        if callable(method):
            mname = method.__name__
        else:
            mname = method
        if self.is_connected:
            try:
                return self.tomcat_major_minor in self._implemented_by.matrix[mname]
            except KeyError:
                return False
        raise TomcatNotConnected("not connected")

    @classmethod
    def implemented_by(
        cls, method: Union[Callable, str], tomcat_major_minor: TomcatMajorMinor
    ) -> bool:
        """Check whether a method is implemented by any version of Tomcat.

        :param method:              a method on :class:`.TomcatManager` to check
        :param tomcat_major_minor:  the version of Tomcat to check
        :return:                   ``True`` if the method is implemented on the
                                    given tomcat version.

        This method does not require prior connection to a Tomcat server.

        .. versionadded:: 3.0.0
        """
        if callable(method):
            mname = method.__name__
        else:
            mname = method
        try:
            return tomcat_major_minor in cls._implemented_by.matrix[mname]
        except KeyError:
            return False

    ###
    # connection property and method
    ###
    @property
    def is_connected(self) -> bool:
        """
        Does the url point to an actual tomcat server and are the credentials valid?

        :return: ``True`` if connected to a tomcat server, otherwise, ``False``.
        """
        return self._url and self._tomcat_major_minor

    def connect(
        self,
        url: str,
        user: str = "",
        password: str = "",
        *,
        cert: Union[str, Tuple[str, str]] = None,
        verify: Union[str, bool] = True,
        timeout: float = None,
    ) -> TomcatManagerResponse:
        """Connect to the manager application running in a Tomcat server.

        :param url:      url where the Tomcat Manager web application is deployed
        :param user:     (optional) user to authenticate with
        :param password: (optional) password to authenticate with
        :param cert:     client side certificates to use for SSL/TLS authentication
        :param verify:   verify server SSL/TLS certificates
        :param timeout:  timeout in seconds for network operations
        :return:         :class:`~tomcatmanager.models.TomcatManagerResponse`
                         object with an additional ``server_info`` attribute

        The ``server_info`` attribute of the returned object contains a
        :class:`.ServerInfo` object, which is a dictionary with some added
        properties for well-known values returned from the Tomcat server.

        This method:

        - sets or changes the url, credentials, and certificates on an existing
          object
        - provides a convenient mechanism to validate you can actually connect
          to the server
        - returns a response object that includes information about the server
          you are connected to
        - allows you to inspect the response so you can see why you can't connect

        **Usage**

        >>> import tomcatmanager as tm
        >>> url = "http://localhost:808099/manager"
        >>> user = "ace"
        >>> password = "newenglandclamchowder"
        >>> tomcat = tm.TomcatManager()
        >>> try:
        ...     r = tomcat.connect(url, user, password)
        ...     if r.ok:
        ...         print("connected")
        ...     else:
        ...         print("not connected")
        ... except Exception as err:
        ...    # handle exception
        ...    print("not connected")
        not connected

        Many things can go wrong when requesting url's via http. tomcatmanager
        uses the `requests <https://docs.python-requests.org/en/master/>`_ library
        for all network communication, and follows that library's approach for
        raising exceptions and checking the response to your request. Therefore:

        - Some exceptions will always be raised by this method. If you give a URL
          where no web server is listening, ``requests.connections.ConnectionError``
          will be raised.
        - Other exceptions will only be raised if you call
          :meth:`.TomcatManagerResponse.raise_for_status()`. For example, if the
          credentials are incorrect, you won't get an exception unless you ask for
          it.
        - The :attr:`.TomcatManagerResponse.ok` attribute is the easiest and most
          rigerous way to check whether you connected successfully. However, as the
          example usage above shows, you still have to catch exceptions because
          `requests <https://docs.python-requests.org/en/master/>`_ can raise
          exceptions from inside the :meth:`.connect` method and this library
          doesn't attempt to catch them so that you can do specific error
          handling if you want to.

        All communications between this library and a Tomcat server happen over HTTP,
        which means there isn't a persistent connection. A new HTTP GET request is
        issued for each method call on this object (i.e. :meth:`~.deploy_localwar`,
        :meth:`~.stop`). However, the mental model for this library is connection
        based: use the :meth:`~.connect` method to establish the URL and authentication
        credentials, then call other methods to perform actions on the server you are
        connected to. If you try and call other methods before you call
        :meth:`~.connect`, :exc:`.TomcatNotConnected` will be raised. Because there
        is no persistent connection of any kind, there is no disconnect method and
        no cleanup to perform when you are done using a server.

        If you discard or don't save the return object from this method, you can call
        :meth:`is_connected` to check if you are connected.

        **Authentication**

        The only way to validate the URL and authentication credentials is to
        make an HTTP request to the server and see if it returns successfully.
        Internally this method tries to retrieve ``/manager/text/serverinfo``.

        Typically authentication is done via user and password. Pass those
        parameters to utilize HTTP Basic authentication.

        To authenticate with a SSL/TLS server using a client certificate and key, pass
        the path to a single file containing the private key and certificate in the
        ``cert`` parameter. As an alternative, you can pass a tuple containing the path
        to the certificate, and the path to the key.

        .. warning::

            The private key for your local certificate must be unencrypted. The
            Requests library used for network communication does not support using
            encrypted keys.

        If the URL uses the ``https`` protocol, the default behavior is to validate
        the server SSL/TLS certificate chain.

        To validate with your own certificate authority bundle, set the
        ``verify`` parameter to the path to a certificate authority bundle file
        or a directory of certificates of trusted certificate authorities. You can
        disable server certificate validation by setting ``verify`` to ``False``.

        See :doc:`/authentication` for more details.

        **Side Effects**

        Passing a ``timeout`` parameter to this method has the side effect of
        setting the :attr:`timeout` attribute on this object.

        Requesting url's via http can also result in redirection to another url. If
        that occurs, the new url, not the one you passed, will be stored in the
        :attr:`url` attribute.

        If you pass user and password credentials and the connection is successful, the
        user will be stored in the :attr:`user` attribute.

        If you pass an authentication key and certificate in the ``cert`` parameter
        and the connection is successful, the information will be stored in the
        :attr:`cert` attribute.

        Upon successful connection, an instance of :class:`.TomcatMajorMinor` will be
        stored in :attr:`tomcat_major_minor` indicating the major version of Tomcat
        running on the server. Further details about the server are available in the
        `server_info` attribute of the returned response.

        .. versionchanged:: 3.0.0

           - Returned :class:`.TomcatManagerResponse` now includes a ``server_info``
             attribute containing a :class:`.ServerInfo` object describing the
             server we are connected to
           - Sets :attr:`tomcat_major_minor` attribute
           - ``timeout`` is now a keyword only argument
        """
        if timeout:
            self.timeout = timeout

        self._clear_server_attrs()
        self._url = url
        self._user = user
        self._password = password
        self._cert = cert
        self._verify = verify
        # don't use server_info() because it will fail because it won't
        # think we are connected to the server yet
        try:
            r = self._get("serverinfo")
            r.server_info = ServerInfo(result=r.result)
            if r.ok:
                self._tomcat_major_minor = r.server_info.tomcat_major_minor
                # _get added /text/serverinfo onto the end of the passed in url
                # we may have been redirected, and we want to store the new
                # url, not the one passed in
                match = re.search(r"(.*)/text/serverinfo$", r.response.url)
                if match:
                    self._url = match.group(1)
            else:
                # don't save the parameters if we don't succeed
                self._clear_server_attrs()
            return r
        except Exception as exc:
            self._clear_server_attrs()
            raise exc

    ###
    # managing applications
    ###
    @_implemented_by(TomcatMajorMinor.supported() + [TomcatMajorMinor.VNEXT])
    def deploy_localwar(
        self, path: str, warfile: str, version: str = None, update: bool = False
    ) -> TomcatManagerResponse:
        """
        Deploy a warfile from the local file system to the Tomcat server.

        :param path:         The path on the server to deploy this war to,
                             i.e. /sampleapp
        :param warfile:      The path (specified using your local operating
                             system convention) to a war file on the local
                             file system. You can also pass a stream or
                             file-like object. This will be sent to the
                             server for deployment.
        :param version:      (optional) For tomcat parallel deployments, the
                             version string to associate with this deployment
        :param update:       (optional) Whether to undeploy the existing path
                             first (default False)
        :return:             :class:`.TomcatManagerResponse` object
        :raises ValueError:  if no path is specified or if no warfile is specified
        """
        params = {}
        if path:
            params["path"] = path
        else:
            raise ValueError("no path specified")
        if not warfile:
            raise ValueError("no warfile specified")
        if version:
            params["version"] = version
        if update:
            params["update"] = "true"

        base = self._url or ""
        url = base + "/text/deploy"
        r = TomcatManagerResponse()
        # have to have the requests.put call in two places so we can
        # properly close the file if we open it
        if self._is_stream(warfile):
            r.response = requests.put(
                url,
                auth=(self._user, self._password),
                params=params,
                data=warfile,
                timeout=self.timeout,
            )
        else:
            with open(warfile, "rb") as warobj:
                r.response = requests.put(
                    url,
                    auth=(self._user, self._password),
                    params=params,
                    data=warobj,
                    timeout=self.timeout,
                )
        return r

    @_implemented_by(TomcatMajorMinor.supported() + [TomcatMajorMinor.VNEXT])
    def deploy_serverwar(
        self, path: str, warfile: str, version: str = None, update: bool = False
    ) -> TomcatManagerResponse:
        """
        Deploy a warfile from the server file system to the Tomcat server.

        :param path:         The path on the server to deploy this war to,
                             i.e. /sampleapp
        :param warfile:      The java-style path (use slashes not backslashes)
                             to the war file on the server. Don't include
                             ``file:`` at the beginning.
        :param version:      (optional) For tomcat parallel deployments, the
                             version string to associate with this deployment
        :param update:       (optional) Whether to undeploy the existing path
                             first (default False)
        :return:             :class:`.TomcatManagerResponse` object
        :raises ValueError:  if no path is given or if no warfile is given
        """
        params = {}
        if path:
            params["path"] = path
        else:
            raise ValueError("no path specified")
        if warfile:
            params["war"] = warfile
        else:
            raise ValueError("no warfile specified")
        if version:
            params["version"] = version
        if update:
            params["update"] = "true"
        r = self._get("deploy", params)
        return r

    @_implemented_by(TomcatMajorMinor.supported() + [TomcatMajorMinor.VNEXT])
    def deploy_servercontext(
        self,
        path: str,
        contextfile: str,
        warfile: str = None,
        version: str = None,
        update: bool = False,
    ) -> TomcatManagerResponse:
        """
        Deploy a Tomcat application defined by a context file from the server
        filesystem to the Tomcat server.

        :param path:         The path on the server to deploy this war to,
                             i.e. /sampleapp
        :param contextfile:  The java-style path (use slashes not backslashes)
                             to the context file on the server. Don't include
                             ``file:`` at the beginning.
        :param warfile:      (optional) The java-style path (use slashes not
                             backslashes) to the war file on the server.
                             Don't include ``file:`` at the beginning.
        :param version:      (optional) For tomcat parallel deployments, the
                             version string to associate with this deployment
        :param update:       (optional) Whether to undeploy the existing path
                             first (default False)
        :return:             :class:`.TomcatManagerResponse` object
        :raises ValueError:  if no path is given or if no contextfile is given
        """
        # pylint: disable=too-many-arguments

        params = {}
        if path:
            params["path"] = path
        else:
            raise ValueError("no path specified")
        if contextfile:
            params["config"] = contextfile
        else:
            raise ValueError("no contextfile specified")
        if warfile:
            params["war"] = warfile
        if version:
            params["version"] = version
        if update:
            params["update"] = "true"
        r = self._get("deploy", params)
        return r

    @_implemented_by(TomcatMajorMinor.supported() + [TomcatMajorMinor.VNEXT])
    def undeploy(self, path: str, version: str = None) -> TomcatManagerResponse:
        """Undeploy an application in the Tomcat server.

        :param path:         The path of the application to undeploy
        :param version:      (optional) The version string of the app to
                             undeploy
        :return:             :class:`.TomcatManagerResponse` object
        :raises ValueError:  if no path is specified

        If the application was deployed with a version string, it must be
        specified in order to undeploy the application.
        """
        params = {}
        if path:
            params = {"path": path}
        else:
            raise ValueError("no path specified")
        if version:
            params["version"] = version
        return self._get("undeploy", params)

    @_implemented_by(TomcatMajorMinor.supported() + [TomcatMajorMinor.VNEXT])
    def start(self, path: str, version: str = None) -> TomcatManagerResponse:
        """
        Start an application already deployed in the Tomcat server.

        :param path:         The path of the application to start
        :param version:      (optional) The version string of the app to start
        :return:             :class:`.TomcatManagerResponse` object
        :raises ValueError:  if no path is specified

        If the application was deployed with a version string, it must be
        specified in order to start the application.
        """
        params = {}
        if path:
            params["path"] = path
        else:
            raise ValueError("no path specified")
        if version:
            params["version"] = version
        return self._get("start", params)

    @_implemented_by(TomcatMajorMinor.supported() + [TomcatMajorMinor.VNEXT])
    def stop(self, path: str, version: str = None) -> TomcatManagerResponse:
        """
        Stop an application already deployed in the Tomcat server.

        :param path:         The path of the application to stop
        :param version:      (optional) The version string of the app to stop
        :return:             :class:`.TomcatManagerResponse` object
        :raises ValueError:  if no path is specified

        If the application was deployed with a version string, it must be
        specified in order to stop the application.
        """
        params = {}
        if path:
            params["path"] = path
        else:
            raise ValueError("no path specified")
        if version:
            params["version"] = version
        return self._get("stop", params)

    @_implemented_by(TomcatMajorMinor.supported() + [TomcatMajorMinor.VNEXT])
    def reload(self, path: str, version: str = None) -> TomcatManagerResponse:
        """
        Stop and start a Tomcat application.

        :param path:         The path of the application to reload
        :param version:      (optional) The version string of the app to reload
        :return:             :class:`.TomcatManagerResponse` object
        :raises ValueError:  if no path is specified

        If the application was deployed with a version string, it must be
        specified in order to reload the application.
        """
        params = {}
        if path:
            params["path"] = path
        else:
            raise ValueError("no path specified")
        if version:
            params["version"] = version
        return self._get("reload", params)

    @_implemented_by(TomcatMajorMinor.supported() + [TomcatMajorMinor.VNEXT])
    def sessions(self, path: str, version: str = None) -> TomcatManagerResponse:
        """
        Get the age of the sessions for an application.

        :param path:         The path of the application to get session
                             information about
        :param version:      (optional) The version string of the app to get
                             session information about
        :return:             :class:`.TomcatManagerResponse` object with the
                             session summary in both the ``result`` attribute
                             and the ``sessions`` attribute
        :raises ValueError:  if no path is specified

        Usage::

            >>> tomcat = getfixture("tomcat")
            >>> r = tomcat.sessions("/manager")
            >>> if r.ok:
            ...     session_data = r.sessions

        """
        params = {}
        if path:
            params["path"] = path
        else:
            raise ValueError("no path specified")
        if version:
            params["version"] = version
        r = self._get("sessions", params)
        if r.ok:
            r.sessions = r.result
        return r

    @_implemented_by(TomcatMajorMinor.supported() + [TomcatMajorMinor.VNEXT])
    def expire(
        self, path: str, version: str = None, idle: Any = None
    ) -> TomcatManagerResponse:
        """
        Expire idle sessions.

        :param path:         the path to the app on the server whose
                             sessions you want to expire
        :param idle:         sessions idle for more than this number of
                             minutes will be expired. Use idle=0 to expire
                             all sessions.
        :return:             :class:`.TomcatManagerResponse` object with the
                             session summary in both the ``result`` attribute
                             and the ``sessions`` attribute
        :raises ValueError:  if no path is specified

        Usage::

            >>> tomcat = getfixture("tomcat")
            >>> r = tomcat.expire("/manager", idle=15)
            >>> if r.ok:
            ...     expiration_data = r.sessions
        """
        params = {}
        if path:
            params["path"] = path
        else:
            raise ValueError("no path specified")
        if version:
            params["version"] = version
        if idle:
            params["idle"] = idle
        r = self._get("expire", params)
        if r.ok:
            r.sessions = r.result
        return r

    @_implemented_by(TomcatMajorMinor.supported() + [TomcatMajorMinor.VNEXT])
    def list(self) -> TomcatManagerResponse:
        """
        Get a list of all applications currently installed.

        :return: :class:`.TomcatManagerResponse` object with an additional
                 ``apps`` attribute which contains a list of
                 :class:`.TomcatApplication` objects

        Usage::

            >>> import tomcatmanager as tm
            >>> tomcat = getfixture("tomcat")
            >>> r = tomcat.list()
            >>> if r.ok:
            ...     running = filter(lambda app: app.state == tm.ApplicationState.RUNNING, r.apps)
        """
        r = self._get("list")
        apps = []
        for line in r.result.splitlines():
            app = TomcatApplication()
            app.parse(line)
            apps.append(app)
        r.apps = apps
        return r

    ###
    #
    # These commands return info about the server
    #
    ###
    @_implemented_by(TomcatMajorMinor.supported() + [TomcatMajorMinor.VNEXT])
    def server_info(self) -> TomcatManagerResponse:
        """
        Get information about the Tomcat server.

        :return: :class:`.TomcatManagerResponse` object with an additional
                 ``server_info`` attribute

        The ``server_info`` attribute contains a :class:`.ServerInfo` object,
        which is a dictionary with some added properties for well-known values
        returned from the Tomcat server.

        Usage::

            >>> tomcat = getfixture("tomcat")
            >>> r = tomcat.server_info()
            >>> if r.ok:
            ...     r.server_info["OS Name"] == r.server_info.os_name
            True

        """
        r = self._get("serverinfo")
        r.server_info = ServerInfo(result=r.result)
        return r

    @_implemented_by(TomcatMajorMinor.supported() + [TomcatMajorMinor.VNEXT])
    def status_xml(self) -> TomcatManagerResponse:
        """
        Get server status information in XML format.

        :return: :class:`.TomcatManagerResponse` object with an additional
                 ``status_xml`` attribute

        Usage::

            >>> import xml.etree.ElementTree as ET
            >>> tomcat = getfixture("tomcat")
            >>> r = tomcat.status_xml()
            >>> if r.ok:
            ...     root = ET.fromstring(r.status_xml)
            ...     mem = root.find("jvm/memory")
            ...     print("Free Memory = {}".format(mem.attrib["free"])) #doctest: +ELLIPSIS
            Free Memory ...

        Tomcat 8.0 doesn't include application info in the XML, even though the docs
        say it does.
        """
        # this command isn't in the /manager/text url space, so we can't use _get()
        base = self._url or ""
        url = base + "/status/all"
        r = TomcatManagerResponse()
        r.response = requests.get(
            url,
            auth=(self._user, self._password),
            params={"XML": "true"},
            timeout=self.timeout,
            verify=self.verify,
            cert=self.cert,
        )
        r.result = r.response.text
        r.status_xml = r.result

        # we have to force a status_code and a status_message
        # because the server doesn't return them
        if r.response.status_code == requests.codes.ok:
            r.status_code = StatusCode.OK
            r.status_message = StatusCode.OK.value
        else:
            r.status_code = StatusCode.FAIL
            r.status_message = StatusCode.FAIL.value
        return r

    @_implemented_by(TomcatMajorMinor.supported() + [TomcatMajorMinor.VNEXT])
    def vm_info(self) -> TomcatManagerResponse:
        """
        Get diagnostic information about the JVM.

        :return: :class:`.TomcatManagerResponse` object with an additional
                 ``vm_info`` attribute
        """
        r = self._get("vminfo")
        r.vm_info = r.result
        return r

    @_implemented_by(TomcatMajorMinor.supported() + [TomcatMajorMinor.VNEXT])
    def thread_dump(self) -> TomcatManagerResponse:
        """
        Get a JVM thread dump.

        :return: :class:`.TomcatManagerResponse` object with an additional
                 ``thread_dump`` attribute
        """
        r = self._get("threaddump")
        r.thread_dump = r.result
        return r

    @_implemented_by(TomcatMajorMinor.supported() + [TomcatMajorMinor.VNEXT])
    def resources(self, type_: str = None) -> TomcatManagerResponse:
        """
        Get the global JNDI resources

        :param type_: (optional) Fully qualified java class name of the
                      resource type you are interested in. For example,
                      pass ``javax.sql.DataSource`` to acquire the names
                      of all available JDBC data sources.
        :return:      :class:`.TomcatManagerResponse` object with an additional
                      ``resources`` attribute.


        Usage::

            >>> tomcat = getfixture("tomcat")
            >>> r = tomcat.resources()
            >>> if r.ok:
            ...     print(r.resources)
            {'UserDatabase': 'org.apache.catalina.users.MemoryUserDatabase'}

        ``resources`` is a dictionary with the resource name as the key
        and the class name as the value.
        """
        if type_:
            r = self._get("resources", {"type": str(type_)})
        else:
            r = self._get("resources")

        resources = {}
        if r.result:
            for line in r.result.splitlines():
                resource, classname = line.rstrip().split(":", 1)
                if resource[:7] != StatusCode.FAIL.value + " - ":
                    resources[resource] = classname.lstrip()
        r.resources = resources
        return r

    @_implemented_by(TomcatMajorMinor.supported() + [TomcatMajorMinor.VNEXT])
    def find_leakers(self) -> TomcatManagerResponse:
        """
        Get apps that leak memory.

        :return: :class:`.TomcatManagerResponse` object with an additional
                 ``leakers`` attribute

        The ``leakers`` attribute contains a list of paths of applications
        which leak memory.

        This command triggers a full garbage collection on the server. Use with
        extreme caution on production systems.

        Explicity triggering a full garbage collection from code is documented to be
        unreliable. Furthermore, depending on the jvm, there are options to disable
        explicit GC triggering, like ``-XX:+DisableExplicitGC``. If you want to make
        sure this command triggered a full GC, you will have to verify using something
        like GC logging or JConsole.

        The Tomcat Manager documentation says the server can return duplicates in this
        list if the app has been reloaded and was leaking both before and after the
        reload. The list returned by the ``leakers`` attribute will have no duplicates in
        it.

        Usage::

            >>> tomcat = getfixture("tomcat")
            >>> r = tomcat.find_leakers()
            >>> if r.ok:
            ...     cnt = len(r.leakers)
            ... else:
            ...     cnt = 0
        """
        r = self._get("findleaks", {"statusLine": "true"})
        r.leakers = self._parse_leakers(r.result)
        return r

    ###
    #
    # ssl related commands
    #
    ###
    @_implemented_by(
        [
            TomcatMajorMinor.V8_0,
            TomcatMajorMinor.V8_5,
            TomcatMajorMinor.V9_0,
            TomcatMajorMinor.V10_0,
            TomcatMajorMinor.VNEXT,
        ]
    )
    def ssl_connector_ciphers(self) -> TomcatManagerResponse:
        """
        Get SSL/TLS ciphers configured for each connector.

        :return: :class:`.TomcatManagerResponse` object with an additional
                 ``ssl_connector_ciphers`` attribute
        """
        r = self._get("sslConnectorCiphers")
        r.ssl_connector_ciphers = r.result
        return r

    @_implemented_by(
        [
            TomcatMajorMinor.V8_5,
            TomcatMajorMinor.V9_0,
            TomcatMajorMinor.V10_0,
            TomcatMajorMinor.VNEXT,
        ]
    )
    def ssl_connector_certs(self) -> TomcatManagerResponse:
        """
        Get the SSL certificate chain currently configured for each virtual host

        :return: :class:`.TomcatManagerResponse` object with an additional
                 ``ssl_connector_certs`` attribute
        """
        r = self._get("sslConnectorCerts")
        r.ssl_connector_certs = r.result
        return r

    @_implemented_by(
        [
            TomcatMajorMinor.V8_5,
            TomcatMajorMinor.V9_0,
            TomcatMajorMinor.V10_0,
            TomcatMajorMinor.VNEXT,
        ]
    )
    def ssl_connector_trusted_certs(self) -> TomcatManagerResponse:
        """
        Get the trusted certificates currently configured for each virtual host

        :return: :class:`.TomcatManagerResponse` object with an additional
                 ``ssl_connector_trusted_certs`` attribute
        """
        r = self._get("sslConnectorTrustedCerts")
        r.ssl_connector_trusted_certs = r.result
        return r

    @_implemented_by(
        [
            TomcatMajorMinor.V8_5,
            TomcatMajorMinor.V9_0,
            TomcatMajorMinor.V10_0,
            TomcatMajorMinor.VNEXT,
        ]
    )
    def ssl_reload(self, host: str = None) -> TomcatManagerResponse:
        """
        Reload TLS certificates and keys (but not server.xml) for a specified or all virtual hosts

        :param host: (optional) Host name to reload, if omitted, reload all virtual hosts

        :return: :class:`.TomcatManagerResponse` object
        """
        if host:
            r = self._get("sslReload", {"tlsHostName": str(host)})
        else:
            r = self._get("sslReload")
        return r

    ###
    #
    # private methods
    #
    ###
    @staticmethod
    def _parse_leakers(text: str) -> List:
        """
        Parse a list of leaking apps from the text returned by tomcat.

        We use this as a separate method for ease of testing against
        several data sets to ensure proper behavior.
        """
        leakers = []
        if text:
            for line in text.splitlines():
                # don't add duplicates
                if not line in leakers:
                    leakers.append(line)
        return leakers

    @classmethod
    def _is_stream(cls, obj) -> bool:
        """return True if passed a stream type object"""
        return all(
            [
                hasattr(obj, "__iter__"),
                not isinstance(obj, (str, bytes, list, tuple, collections.abc.Mapping)),
            ]
        )

    def _clear_server_attrs(self):
        """
        Clear the private attributes describing the server.

        Intended to be called from connect() and is_connected()
        """
        self._user = None
        self._password = None
        self._url = None
        self._cert = None
        self._verify = None
        self._tomcat_major_minor = None

    def _get(self, cmd: str, payload: dict = None) -> TomcatManagerResponse:
        """
        Make an HTTP get request to the tomcat manager web app.

        :param cmd:     name of the command from the tomcat server url
                        i.e. 'http://localhost:8080/manager/text/{cmd}
        :param payload: dict of params for `requests.get()`
        :return:        `TomcatManagerResponse` object
        """
        base = self._url or ""
        # if we have no url, don't add other stuff to it because it makes
        # the exceptions hard to understand
        if base:
            url = base + "/text/" + cmd
        else:
            url = ""
        authinfo = None
        if self._user and self._password:
            authinfo = (self._user, self._password)

        r = TomcatManagerResponse()
        r.response = requests.get(
            url,
            auth=authinfo,
            params=payload,
            timeout=self.timeout,
            verify=self.verify,
            cert=self.cert,
        )
        return r
