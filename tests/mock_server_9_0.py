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
Mock up a Tomcat Manager application that behaves like tomcat version 9.0.x
"""

import socket
import threading
from http.server import HTTPServer

from tests.mock_server_ssl import MockRequestHandlerSSL


class MockRequestHandler90(MockRequestHandlerSSL):
    """Handle HTTP Requests like Tomcat Manager 9.0.x"""

    def get_server_info(self):
        """Send the server information."""
        self.send_text(
            """OK - Server info
Tomcat Version: [Apache Tomcat/9.0.45]
OS Name: [Linux]
OS Version: [5.4.0-67-generic]
OS Architecture: [amd64]
JVM Version: [1.8.0_282-8u282-b08-0ubuntu1~20.04-b08]
JVM Vendor: [Private Build]"""
        )


def start_mock_server_9_0(tms):
    """Start a mock Tomcat Manager application

    :return: a tuple: (url, user, password) where the server is accessible
    """
    # pylint: disable=unused-variable
    # go find an unused port
    sock = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
    sock.bind(("localhost", 0))
    _, port = sock.getsockname()
    sock.close()

    tms.url = f"http://localhost:{port}/manager"
    tms.user = MockRequestHandler90.USER
    tms.password = MockRequestHandler90.PASSWORD
    tms.cert = None
    tms.warfile = "/path/to/server.war"
    tms.contextfile = "path/to/context.xml"
    tms.connect_command = f"connect {tms.url} {tms.user} {tms.password}"

    mock_server = HTTPServer(("localhost", port), MockRequestHandler90)
    mock_server_thread = threading.Thread(target=mock_server.serve_forever)
    mock_server_thread.daemon = True
    mock_server_thread.start()

    return (mock_server, tms)
