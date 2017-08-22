#
# -*- coding: utf-8 -*-

import os
import pytest

import tomcatmanager as tm
from tests.mock_server80 import start_mock_server80

###
#
# add command line options
#
###
def pytest_addoption(parser):
    parser.addoption("--url", action="store", default=None,
        help="url: url of tomcat manager to test against instead of mock")
    parser.addoption("--user", action="store", default=None,
        help="user: use to authenticate")
    parser.addoption("--password", action="store", default=None,
        help="password: use to authenticate")
    parser.addoption("--serverwar", action="store", default=None,
        help="serverwar: path to deployable war file on the tomcat server")

###
#
# fixtures for testing TomcatManager()
#
###
@pytest.fixture(scope='module')
def tomcat_manager_server(request):
    """start a local http server which provides a similar interface to a real Tomcat Manager app"""
    url = request.config.getoption("--url")
    if url:
        # use the server info specified on the command line
        tms = {'url': url}
        user = request.config.getoption("--user")
        tms.update({'user': user})
        password = request.config.getoption("--password")
        tms.update({'password': password})
        return tms
    else:
        # go start up a fake server
        return start_mock_server80()

@pytest.fixture(scope='module')
def serverwar_file(request):
    war = request.config.getoption("--serverwar")
    if not war:
        war = '/tmp/sample.war'
    return war    

@pytest.fixture(scope='module')
def tomcat(tomcat_manager_server):
    tomcat = tm.TomcatManager()
    r = tomcat.connect(
            tomcat_manager_server['url'],
            tomcat_manager_server['user'],
            tomcat_manager_server['password']
        )
    return tomcat

@pytest.fixture(scope='module')
def localwar_file():
    """return the path to a valid war file"""
    return os.path.dirname(__file__) + '/tests/war/sample.war'

@pytest.fixture(scope='module')
def safe_path():
    """a safe path we can deploy apps to"""
    return '/tomcat-manager-test-app'

@pytest.fixture(scope='module')
def server_info():
    return """Tomcat Version: Apache Tomcat/8.0.32 (Ubuntu)
OS Name: Linux
OS Version: 4.4.0-89-generic
OS Architecture: amd64
JVM Version: 1.8.0_131-8u131-b11-2ubuntu1.16.04.3-b11
JVM Vendor: Oracle Corporation
"""

