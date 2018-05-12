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

This module contains the data objects created by and used by tomcatmanager.
"""

from typing import TypeVar

from attrdict import AttrDict
import requests

import tomcatmanager as tm


class TomcatError(Exception):
    """
    Raised when the Tomcat Server responds with an error.
    """
    pass

###
#
# build status codes
#
###
STATUS_CODES = {
    # 'sent from tomcat': 'friendly name'
    'OK': 'ok',
    'FAIL': 'fail',
    # if we can't find tomcat, we invent a NOTFOUND value
    'NOTFOUND': 'notfound',
}
# pylint: disable=invalid-name
status_codes = AttrDict()
for _code, _title in STATUS_CODES.items():
    status_codes[_title] = _code


class TomcatManagerResponse:
    """
    Returned as the response for :class:`TomcatManager` commands.

    After running a command, it's a good idea to check and make sure that
    the command completed succesfully before relying on the results::

        >>> import tomcatmanager as tm
        >>> tomcat = getfixture('tomcat')
        >>> try:
        ...     r = tomcat.server_info()
        ...     r.raise_for_status()
        ...     if r.ok:
        ...         print(r.server_info.os_name)
        ...     else:
        ...         print('Error: {}'.format(r.status_message))
        ... except Exception as err:
        ...     # handle exception
        ...     pass
        Linux

    """

    def __init__(self, response=None):
        self._response = response
        self._status_code = None
        self._status_message = None
        self._result = None

    @property
    def ok(self):
        """
        :return: True if the request completed with no errors.

        For this property to return True:

        - The HTTP request must return a status code of ``200 OK``
        - The first line of the response from the Tomcat Server must begin with ``OK``.
        """
        return all([
            self.response != None,
            self.response.status_code == requests.codes.ok,
            self.status_code == tm.status_codes.ok,
            ])

    def raise_for_status(self):
        """
        Raise exceptions for server errors.

        First call `requests.Response.raise_for_status()` which
        raises exceptions if a 4xx or 5xx response is received from the
        server.

        If that doesn't raise anything, then raise a `TomcatError`
        if there is not an ``OK`` response from the first line of text back
        from the Tomcat Manager web app.
        """
        self.response.raise_for_status()
        if self.status_code != tm.status_codes.ok:
            raise TomcatError(self.status_message)

    @property
    def status_code(self):
        """
        Status of the Tomcat Manager command from the first line of text.

        The preferred way to check for success is to use the `ok()` method,
        because it checks for http errors as well as tomcat errors.
        However, if you want specific access to the status of the tomcat
        command, use this method.

        There are three status codes:

        - ``OK``
        - ``FAIL``
        - ``NOTFOUND``

        `tomcatmanager.status_codes` is a dictionary which makes it easy to
        check `status_code` against known values. It also has attributes with
        friendly names, as shown here::

            >>> import tomcatmanager as tm
            >>> tomcat = getfixture('tomcat')
            >>> r = tomcat.server_info()
            >>> r.status_code == tm.status_codes.ok
            True
        """
        return self._status_code

    @status_code.setter
    def status_code(self, value: str):
        self._status_code = value

    @property
    def status_message(self):
        """
        The message on the first line of the response from the Tomcat Server.
        """
        return self._status_message

    @status_message.setter
    def status_message(self, value: str):
        self._status_message = value

    @property
    def result(self):
        """
        The text of the response from the Tomcat server, without the first
        line (which contains the status code and message).
        """
        return self._result

    @result.setter
    def result(self, value: str):
        self._result = value

    @property
    def response(self) -> requests.models.Response:
        """
        The server's response to an HTTP request.

        `TomcatManager` uses the excellent Requests package for HTTP
        communication. This property returns the `requests.models.Response`
        object which contains the server's response to the HTTP request.

        Of particular use is `requests.models.Response.text` which
        contains the content of the response in unicode. If you want raw access to
        the content returned by the Tomcat Server, this is where you can get it.
        """
        return self._response

    @response.setter
    def response(self, response: requests.models.Response):
        self._response = response
        # parse the text to get the status code and results
        if response.text:
            lines = response.text.splitlines()
            # get the status line, if the request completed OK
            if response.status_code == requests.codes.ok:
                try:
                    statusline = response.text.splitlines()[0]
                    code = statusline.split(' ', 1)[0]
                    if code in tm.status_codes.values():
                        self.status_code = code
                        self.status_message = statusline.split(' ', 1)[1][2:]
                        if len(lines) > 1:
                            self.result = "\n".join(lines[1:])
                    else:
                        self.status_code = tm.status_codes.notfound
                        self.status_message = 'Tomcat Manager not found'
                except IndexError:
                    pass


APPLICATION_STATES = [
    'running',
    'stopped',
]
application_states = AttrDict()
for _state in APPLICATION_STATES:
    application_states[_state] = _state

TA = TypeVar('TA', bound='TomcatApplication')
class TomcatApplication():
    """
    Discrete data about an application running inside a Tomcat Server.

    A list of these objects is returned by :meth:`tomcatmanager.TomcatManager.list`.
    """
    @classmethod
    def sort_by_state_by_path_by_version(cls, app: TA):
        """
        Function to create a key usable by `sort` to sort by state, by path, by version.
        """
        return '{}:{}:{}'.format(
            app.state or '',
            app.path or '',
            app.version or ''
            )

    @classmethod
    def sort_by_path_by_version_by_state(cls, app: TA):
        """
        Function to create a key usable by `sort` to sort by path, by version, by state
        """
        return '{}:{}:{}'.format(
            app.path or '',
            app.version or '',
            app.state or ''
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
        sessions = ''
        if self.sessions is not None:
            sessions = self.sessions
        return fmt.format(
            self.path or '',
            self.state or '',
            sessions,
            self.directory_and_version or ''
            )

    def __lt__(self, other: TA):
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

        .. code-block:: none

           /shiny:running:0:shiny##v2.0.6

        The data elements in this line can be described as:

        .. code-block:: none

           {path}:{state}:{sessions}:{directory}##{version}

        Where version and the two hash marks that precede it are optional.
        """
        app_details = line.rstrip().split(":")
        self._path, self._state, sessions, dirver = app_details[:4]
        self._sessions = int(sessions)
        dirver = dirver.split('##')
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

        `tomcatmanager.application_states` is a dictionary of all the valid
        values for this property. In addition to being a dictionary, it also has
        attributes for each possible state::

            >>> import tomcatmanager as tm
            >>> tm.application_states['stopped']
            'stopped'
            >>> tm.application_states.running
            'running'
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
                dandv += '##{}'.format(self.version)
        return dandv


class ServerInfo(dict):
    """
    Discrete data about the Tomcat server.

    This object is a dictionary of keys and values as returned from the
    Tomcat server. It also has properties for well-known values.

    Usage::

        >>> tomcat = getfixture('tomcat')
        >>> r = tomcat.server_info()
        >>> r.server_info['OS Architecture']
        'amd64'
        >>> r.server_info.jvm_vendor
        'Oracle Corporation'
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize from the plain text response from a Tomcat server.

        :param result: the plain text from the server, minus the first
        line with the status info
        """
        super().__init__(*args, **kwargs)
        self._tomcat_version = None
        self._os_name = None
        self._os_version = None
        self._os_architecture = None
        self._jvm_version = None
        self._jvm_vendor = None
        result = kwargs.pop('result', None)
        self._parse(result)

    def _parse(self, result: str):
        """Parse up a list of lines from the server."""
        if result:
            for line in result.splitlines():
                key, value = line.rstrip().split(':', 1)
                self[key] = value.lstrip()

            self._tomcat_version = self['Tomcat Version']
            self._os_name = self['OS Name']
            self._os_version = self['OS Version']
            self._os_architecture = self['OS Architecture']
            self._jvm_version = self['JVM Version']
            self._jvm_vendor = self['JVM Vendor']

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
