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
~~~~~~~~~~~~~~~

This module contains the data objects created by and used by tomcatmanager.
"""

import requests
from requests.structures import LookupDict


class TomcatError(Exception):
	pass


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
            self.status_code == codes.ok,
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
        if self.status_code != codes.ok:
            raise TomcatError(self.status_message)

    @property
    def status_code(self):
        """
        Status of the Tomcat Manager command from the first line of text.

        The preferred way to check for success is to use the `ok()` method,
        because it checks for http errors as well as tomcat errors.
        However, if you want specific access to the status of the tomcat
        command, use this method.
        
        Currently there are only two known status codes
        
        - ``OK``
        - ``FAIL``
        
        A lookup object, `tomcatmanager.codes`, makes it easy to check
        `status_code` against known values::

            >>> import tomcatmanager as tm
            >>> tomcat = getfixture('tomcat')
            >>> r = tomcat.server_info()
            >>> r.status_code == tm.codes.ok
            True
        """
        return self._status_code

    @status_code.setter
    def status_code(self, value):
        self._status_code = value

    @property
    def status_message(self):
        """
        The message on the first line of the response from the Tomcat Server.
        """
        return self._status_message
    
    @status_message.setter
    def status_message(self, value):
        self._status_message = value

    @property
    def result(self):
        """
        The text of the response from the Tomcat server, without the first
        line (which contains the status code and message).
        """
        return self._result

    @result.setter
    def result(self, value):
        self._result = value

    @property
    def response(self):
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
    def response(self, response):
        self._response = response
        # parse the text to get the status code and results
        if response.text:
            lines = response.text.splitlines()
            # get the status line
            try:
                statusline = response.text.splitlines()[0]
                self.status_code = statusline.split(' ', 1)[0]
                self.status_message = statusline.split(' ',1)[1][2:]
            except IndexError:
                pass
            # set the result
            try:
                self.result = "\n".join(lines[1:])
            except IndexError:
                pass


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

    def __init__(self, result=None):
        """
        Initialize from the plain text response from a Tomcat server.
        
        :param result: the plain text from the server, minus the first
        line with the status info
        """
        self._tomcat_version = None
        self._os_name = None
        self._os_version= None
        self._os_architecture = None
        self._jvm_version = None
        self._jvm_vendor = None
        self._parse(result)

    def _parse(self, result):
        """Parse up a list of lines from the server."""
        if result:
            for line in result.splitlines():
                key, value = line.rstrip().split(':',1)
                self[key] = value.lstrip()
        
            self._tomcat_version = self['Tomcat Version']
            self._os_name = self['OS Name']
            self._os_version= self['OS Version']
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

###
#
# build status codes
#
###
_codes = {

    # 'sent from tomcat': 'friendly name'
    'OK': 'ok',
    'FAIL': 'fail',
}

codes = LookupDict(name='status_codes')

for code, title in _codes.items():
    setattr(codes, title, code)
