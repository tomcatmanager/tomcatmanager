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

import os
import pytest

from tests.mock_server80 import start_mock_server80
import tomcatmanager as tm


@pytest.fixture(scope='module')
def mock_server80():
    """start a local http server which provides a similar interface to a real Tomcat Manager app"""
    return start_mock_server80()

@pytest.fixture(scope='module')
def tomcat(mock_server80):
    return tm.TomcatManager(
            mock_server80['url'],
            mock_server80['userid'],
            mock_server80['password'] )

@pytest.fixture(scope='module')
def war_file():
    """return the path to a valid war file"""
    return os.path.dirname(__file__) + '/war/sample.war'

@pytest.fixture(scope='function')
def war_fileobj(war_file):
    """open war_file for binary reading"""
    return open(war_file, 'rb')

@pytest.fixture(scope='module')
def server_info_lines():
    result = """Tomcat Version: Apache Tomcat/8.0.32 (Ubuntu)
OS Name: Linux
OS Version: 4.4.0-89-generic
OS Architecture: amd64
JVM Version: 1.8.0_131-8u131-b11-2ubuntu1.16.04.3-b11
JVM Vendor: Oracle Corporation
"""
    return result.splitlines()
