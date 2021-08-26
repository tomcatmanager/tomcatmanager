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
"""
tomcatmanager.models
--------------------

This module contains the data objects created and used by tomcatmanager.
"""

import enum
import re
from typing import List

import requests

import tomcatmanager as tm


class TomcatError(Exception):
    """
    Raised when the Tomcat Server responds with an error.
    """


class TomcatNotImplementedError(Exception):
    """
    Raised when a Tomcat Manager web application does not support a python
    API call.

    .. versionadded:: 3.0.0
    """


class TomcatNotConnected(Exception):
    """
    Raised when a method is called on :class:`.TomcatManager` without the
    :meth:`~.TomcatManager.connect()` method being called first.

    .. versionadded:: 3.0.0
    """


@enum.unique
class StatusCode(enum.Enum):
    """An enumeration of the various Tomcat Manager web application status codes

    ``tomcatmanager`` uses the excellent `requests <https://github.com/psf/requests>`_
    library, which uses a custom ``LookupDict`` class to store HTTP status codes in a
    dictionary. After much debate on whether we should do it the requests way, or
    a more pythonic way, I chose to use a native Enum class instead.

    .. versionadded:: 2.0.0
    """

    OK = "OK"
    FAIL = "FAIL"
    NOTFOUND = "NOTFOUND"

    @classmethod
    def parse(cls, code: str):
        """Return one of the enums from a string sent by the Tomcat Manager
        web application.

        :param state: the string value of the status code from the
            tomcat server
        :type state: str
        :return: :class:`.StatusCode` instance
        :rtype:  tomcatmanager.models.StatusCode
        :raises ValueError: if the string does not represent a known status code
        """
        for _, member in cls.__members__.items():
            if code == member.value:
                return member
        raise ValueError("{} is an unknown status code".format(code))


# pylint: disable=too-many-instance-attributes
class TomcatManagerResponse:
    """
    Returned as the response for :class:`.TomcatManager` commands.

    After running a command, it's a good idea to check and make sure that
    the command completed succesfully before relying on the results::

        >>> import tomcatmanager as tm
        >>> tomcat = getfixture("tomcat")
        >>> try:
        ...     r = tomcat.server_info()
        ...     r.raise_for_status()
        ...     if r.ok:
        ...         print("Operating System: {}".format(r.server_info.os_name))
        ...     else:
        ...         print("Error: {}".format(r.status_message))
        ... except Exception as err:
        ...     # handle exception
        ...     pass
        Operating System: ...

    """

    def __init__(self, response=None):
        self._response = response

        self.status_code = None
        """Status of the Tomcat Manager command from the first line of text.

        The preferred way to check for success is to use the
        :meth:`~.TomcatManagerResponse.ok` method, because it checks for http
        errors as well as tomcat errors. However, if you want specific access
        to the status of the tomcat command, use this method.

        The status codes are enumerated in :class:`StatusCode`.

            >>> import tomcatmanager as tm
            >>> tomcat = getfixture("tomcat")
            >>> r = tomcat.server_info()
            >>> r.status_code == tm.StatusCode.OK
            True
        """

        self.status_message = None
        """The message on the first line of the response from the Tomcat Server.
        """

        self.result = None
        """The text of the response from the Tomcat server, without the first line
        (which contains the status code and message).
        """

    @property
    def ok(self):
        """
        :return: True if the request completed with no errors.

        For this property to return True:

        - The HTTP request must return a status code of ``200 OK``
        - The first line of the response from the Tomcat Manager web application
          must begin with ``OK``.
        """
        return all(
            [
                self.response is not None,
                self.response.status_code == requests.codes.ok,
                self.status_code == tm.StatusCode.OK,
            ]
        )

    def raise_for_status(self):
        """
        Raise exceptions for server errors.

        First this method calls ``requests.Response.raise_for_status()`` which
        raises exceptions if a 4xx or 5xx response is received from the server.

        If that doesn't raise anything, then it raises a :class:`TomcatError`
        if there is not an ``OK`` response from the first line of text back
        from the Tomcat Manager web app.
        """
        self.response.raise_for_status()
        if self.status_code != tm.StatusCode.OK:
            raise TomcatError(self.status_message)

    @property
    def response(self) -> requests.models.Response:
        """
        The server's response to an HTTP request.

        :class:`.TomcatManager` uses the excellent Requests package for HTTP
        communication. This property returns the ``requests.models.Response``
        object which contains the server's response to the HTTP request.

        Of particular use is ``requests.models.Response.text`` which contains
        the content of the response in unicode. If you want raw access to the
        content returned by the Tomcat Server, this is where you can get it.
        """
        return self._response

    @response.setter
    def response(self, response: requests.models.Response):
        self._response = response
        # parse the text to get the status code and results
        if response.text:
            lines = response.text.splitlines()
            try:
                statusline = response.text.splitlines()[0]
                codestr = statusline.split(" ", 1)[0]
                code = StatusCode.parse(codestr)
                self.status_code = code
                self.status_message = statusline.split(" ", 1)[1][2:]
                if len(lines) > 1:
                    self.result = "\n".join(lines[1:])
            except (IndexError, ValueError):
                self.status_code = tm.StatusCode.NOTFOUND
                self.status_message = "Tomcat Manager not found"


@enum.unique
class ApplicationState(enum.Enum):
    """An enumeration of the various tomcat application states.

    .. versionadded:: 2.0.0
    """

    RUNNING = "running"
    STOPPED = "stopped"

    @classmethod
    def parse(cls, state: str):
        """Return one of the enums from a string sent by the Tomcat Manager
        web application.

        :param state: the string value of the application state from the
            tomcat server
        :type state: str
        :return: :class:`.ApplicationState` instance
        :rtype:  tomcatmanager.models.ApplicationState
        :raises ValueError: if the string does not represent a known application state
        """
        for _, member in cls.__members__.items():
            if state == member.value:
                return member
        raise ValueError("{} is an unknown application state".format(state))


class TomcatApplication:
    """
    Discrete data about an application running inside a Tomcat Server.

    A list of these objects is returned by :meth:`.TomcatManager.list`.
    """

    @classmethod
    def sort_by_state_by_path_by_version(cls, app: "TomcatApplication"):
        """
        Create a key usable by ``sort`` to sort by state, by path, by version.
        """
        return "{}:{}:{}".format(
            app.state.value or "", app.path or "", app.version or ""
        )

    @classmethod
    def sort_by_path_by_version_by_state(cls, app: "TomcatApplication"):
        """
        Create a key usable by ``sort`` to sort by path, by version, by state
        """
        return "{}:{}:{}".format(
            app.path or "", app.version or "", app.state.value or ""
        )

    def __init__(self):
        self._path = None
        self._state = None
        self._sessions = None
        self._directory = None
        self._version = None

    def __str__(self):
        """Format this application as it comes from the tomcat server."""
        fmt = "{}:{}:{}:{}"
        sessions = ""
        if self.sessions is not None:
            sessions = self.sessions
        return fmt.format(
            self.path or "",
            self.state.value or "",
            sessions,
            self.directory_and_version or "",
        )

    def __lt__(self, other: "TomcatApplication"):
        """
        Compare one object to another. Useful for sorting lists of apps.

        The sort order is by state (as string), by path (as string), by version
        (by string, if present).
        """
        self_key = self.sort_by_state_by_path_by_version(self)
        other_key = self.sort_by_state_by_path_by_version(other)
        return self_key < other_key

    def parse(self, line: str):
        """
        Parse a line from the server into this object.

        :param: line - the line of text from Tomcat Manager describing
                       a deployed application

        Tomcat Manager outputs a line like this for each application:

        .. code-block::

           /shiny:running:0:shiny##v2.0.6

        The data elements in this line can be described as:

        .. code-block::

           {path}:{state}:{sessions}:{directory}##{version}

        Where version and the two hash marks that precede it are optional.
        """
        app_details = line.rstrip().split(":")
        self._path, state, sessions, dirver = app_details[:4]
        self._state = ApplicationState.parse(state)
        self._sessions = int(sessions)
        dirver = dirver.split("##")
        self._directory = dirver[0]
        if len(dirver) == 1:
            self._version = None
        else:
            self._version = dirver[1]

    @property
    def path(self):
        """
        The context path, or relative URL, where this app is available on the server.
        """
        return self._path

    @property
    def state(self):
        """
        The current state of the application.

        ``tomcatmanager.ApplicationState`` is an enum of the values for this
        property.

            >>> import tomcatmanager as tm
            >>> tm.ApplicationState.STOPPED
            <ApplicationState.STOPPED: 'stopped'>
            >>> tm.ApplicationState.RUNNING
            <ApplicationState.RUNNING: 'running'>
        """
        return self._state

    @property
    def sessions(self):
        """
        The number of currently active sessions.
        """
        return self._sessions

    @property
    def directory(self):
        """
        The directory on the server where this application resides.
        """
        return self._directory

    @property
    def version(self):
        """
        The version of the application given when it was deployed.

        If deployed without a version, this property returns None.
        """
        return self._version

    @property
    def directory_and_version(self):
        """
        Combine directory and version together.

        Tomcat provides this information as ``{directory}`` if there was no
        version specified when the application was deployed, or
        ``{directory}##{version}`` if the version was specified.

        This method has the logic to determine if version was specified or not.
        """
        dandv = None
        if self.directory:
            dandv = self.directory
            if self.version:
                dandv += "##{}".format(self.version)
        return dandv


# type annotations on some class methods reference itself, which generates an error
# because the type has not yet been defined. Will be fixed in Python 3.10, see PEP 484
# and PEP 563. Until this, we store the type annotations as strings
@enum.unique
class TomcatMajorMinor(enum.Enum):
    """An enumeration of the supported Tomcat major and minor version numbers

    Major and Minor have the meanings defined at `https://semver.org
    <https://semver.org>`_.

    This enumeration includes a value VNEXT, so that this module can mostly keep working
    when accessing a version of Tomcat that the module doesn't officially support yet.

    It also includes a value UNSUPPORTED, for older versions of Tomcat that are unknown
    to this module.

    .. versionadded:: 3.0.0

    """

    V8_0 = "8.0"
    V8_5 = "8.5"
    V9_0 = "9.0"
    V10_0 = "10.0"
    VNEXT = "next"
    UNSUPPORTED = "unsupported"

    @classmethod
    def parse(cls, version_string: str) -> "TomcatMajorMinor":
        """Return one of the enums from a string sent by the Tomcat Manager
        web application.

        :param version_string: the string value of the application state from the
            tomcat server
        :return: :class:`.TomcatMajorMinor` instance
        :raises ValueError: if the version string does not represent a known app
        """
        version_re = re.compile(r"(\d+)\.(\d+)\.(\d+)")
        match = version_re.search(version_string)
        ver = TomcatMajorMinor.UNSUPPORTED
        if match:
            # shouldn't ever throw exceptions because of the regex
            major_ver = int(match.group(1))
            minor_ver = int(match.group(2))
            if major_ver < 8:
                ver = TomcatMajorMinor.UNSUPPORTED
            elif major_ver == 8 and minor_ver == 0:
                ver = TomcatMajorMinor.V8_0
            elif major_ver == 8 and minor_ver == 5:
                ver = TomcatMajorMinor.V8_5
            elif major_ver == 9 and minor_ver == 0:
                ver = TomcatMajorMinor.V9_0
            elif major_ver == 10 and minor_ver == 0:
                ver = TomcatMajorMinor.V10_0
            elif major_ver == 10 and minor_ver > 0:
                ver = TomcatMajorMinor.VNEXT
            elif major_ver > 10:
                ver = TomcatMajorMinor.VNEXT
        return ver

    @staticmethod
    def supported() -> List:
        """
        Return the list of officially supported Tomcat major versions
        """
        return [
            TomcatMajorMinor.V8_0,
            TomcatMajorMinor.V8_5,
            TomcatMajorMinor.V9_0,
            TomcatMajorMinor.V10_0,
        ]

    @classmethod
    def lowest_supported(cls) -> "TomcatMajorMinor":
        """
        Return the lowest officially supported Tomcat major version
        """
        return TomcatMajorMinor.supported()[0]

    @classmethod
    def highest_supported(cls) -> "TomcatMajorMinor":
        """
        Return the highest officially supported Tomcat major version

        This does not include ``TomcatMajorMinor.VNEXT``, which exists to ensure this
        module mostly works on future versions of tomcat before official support
        is added.
        """
        return TomcatMajorMinor.supported()[-1]


class ServerInfo(dict):
    """
    Discrete data about the Tomcat server.

    This object is a dictionary of keys and values as returned from the
    Tomcat server. It also has properties for well-known values.

    Usage::

        >>> tomcat = getfixture('tomcat')
        >>> r = tomcat.server_info()
        >>> r.server_info['OS Architecture'] # doctest: +ELLIPSIS
        '...'
        >>> r.server_info.jvm_vendor # doctest: +ELLIPSIS
        '...'
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize from the plain text response from a Tomcat server.

        :param result: the plain text from the server, minus the first
        line with the status info
        """
        super().__init__(*args, **kwargs)
        self._tomcat_major_minor = None
        self._tomcat_version = None
        self._os_name = None
        self._os_version = None
        self._os_architecture = None
        self._jvm_version = None
        self._jvm_vendor = None
        result = kwargs.pop("result", None)
        self._parse(result)

    def _parse(self, result: str):
        """Parse up a list of lines from the server."""
        if result:
            for line in result.splitlines():
                key, value = line.rstrip().split(":", 1)
                self[key] = value.lstrip()
            self._tomcat_version = self["Tomcat Version"]
            self._tomcat_major_minor = TomcatMajorMinor.parse(self._tomcat_version)
            self._os_name = self["OS Name"]
            self._os_version = self["OS Version"]
            self._os_architecture = self["OS Architecture"]
            self._jvm_version = self["JVM Version"]
            self._jvm_vendor = self["JVM Vendor"]

    @property
    def tomcat_major_minor(self) -> TomcatMajorMinor:
        """An instance of :class:`~.models.TomcatMajorMinor` indicating which
        major and minor version of Tomcat is running on the server.

        This value is computed, not received from the server, and therefore does not
        show up in the dictionary, ie ``server_info["tomcat_major_minor"]`` does
        not exist.

        .. versionadded:: 3.0.0
        """
        return self._tomcat_major_minor

    @property
    def tomcat_version(self):
        """The tomcat version string."""
        return self._tomcat_version

    @property
    def os_name(self):
        """The operating system name."""
        return self._os_name

    @property
    def os_version(self):
        """The operating system version."""
        return self._os_version

    @property
    def os_architecture(self):
        """The operating system architecture."""
        return self._os_architecture

    @property
    def jvm_version(self):
        """The java virtual machine version string."""
        return self._jvm_version

    @property
    def jvm_vendor(self):
        """The java virtual machine vendor."""
        return self._jvm_vendor
