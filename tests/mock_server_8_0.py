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
# pylint: disable=too-many-lines, too-many-public-methods

"""
Mock up a Tomcat Manager application that behaves like tomcat version 8.0.x
"""

import re
from http.server import HTTPServer
import socket
import threading

from tests.mock_server_nossl import MockRequestHandlerNoSSL


def requires_authorization(func):
    """Decorator for methods which require authorization."""

    def _requires_authorization(self, *args, **kwargs):
        if self.authorized():
            func(self, *args, **kwargs)

    return _requires_authorization


class MockRequestHandler80(MockRequestHandlerNoSSL):
    """Handle HTTP Requests like Tomcat Manager 8.0.x"""

    SSL_PATTERN = re.compile(r"^/manager/text/sslConnectorCiphers($|\?.*$)")

    # pylint: disable=too-many-branches, invalid-name
    @requires_authorization
    def do_GET(self):
        """Handle all HTTP GET requests."""
        # handle request based on path
        if re.search(self.TEXT_PATTERN, self.path):
            self.send_fail("Unknown command")

        # the info commands
        elif re.search(self.LIST_PATTERN, self.path):
            self.get_list()
        elif re.search(self.SERVER_INFO_PATTERN, self.path):
            self.get_server_info()
        elif re.search(self.STATUS_PATTERN, self.path):
            self.get_status()
        elif re.search(self.VM_INFO_PATTERN, self.path):
            self.get_vm_info()
        elif re.search(self.SSL_PATTERN, self.path):
            self.get_ssl_connector_ciphers()
        elif re.search(self.THREAD_DUMP_PATTERN, self.path):
            self.get_thread_dump()
        elif re.search(self.RESOURCES_PATTERN, self.path):
            self.get_resources()
        elif re.search(self.FIND_LEAKERS_PATTERN, self.path):
            self.get_find_leakers()
        elif re.search(self.SESSIONS_PATTERN, self.path):
            self.get_sessions()

        # the action commands
        elif re.search(self.EXPIRE_PATTERN, self.path):
            self.get_expire()
        elif re.search(self.START_PATTERN, self.path):
            self.get_start()
        elif re.search(self.STOP_PATTERN, self.path):
            self.get_stop()
        elif re.search(self.RELOAD_PATTERN, self.path):
            self.get_reload()
        elif re.search(self.DEPLOY_PATTERN, self.path):
            self.get_deploy()
        elif re.search(self.UNDEPLOY_PATTERN, self.path):
            self.get_undeploy()

        # fail if we don't recognize the path
        else:
            self.send_fail("Unknown command")

    def get_server_info(self):
        """Send the server information."""
        self.send_text(
            """OK - Server info
Tomcat Version: Apache Tomcat/8.0.32 (Ubuntu)
OS Name: Linux
OS Version: 4.4.0-89-generic
OS Architecture: amd64
JVM Version: 1.8.0_131-8u131-b11-2ubuntu1.16.04.3-b11
JVM Vendor: Oracle Corporation"""
        )

    def get_ssl_connector_ciphers(self):
        """Send the SSL ciphers."""
        self.send_text(
            """OK - Connector / SSL Cipher information
Connector[HTTP/1.1-8080]
  SSL is not enabled for this connector"""
        )


###
#
#
###
def start_mock_server_8_0(tms):
    """Start a mock Tomcat Manager application

    :return: a tuple: (url, user, password) where the server is accessible
    """
    # pylint: disable=unused-variable
    # go find an unused port
    sock = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
    sock.bind(("localhost", 0))
    address, port = sock.getsockname()
    sock.close()

    tms.url = "http://localhost:{}/manager".format(port)
    tms.user = MockRequestHandler80.USER
    tms.password = MockRequestHandler80.PASSWORD
    tms.cert = None
    tms.warfile = "/path/to/server.war"
    tms.contextfile = "path/to/context.xml"
    tms.connect_command = "connect {} {} {}".format(tms.url, tms.user, tms.password)

    mock_server = HTTPServer(("localhost", port), MockRequestHandler80)
    mock_server_thread = threading.Thread(target=mock_server.serve_forever)
    mock_server_thread.daemon = True
    mock_server_thread.start()

    return (mock_server, tms)
