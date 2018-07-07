#
# -*- coding: utf-8 -*-

import os

import pytest
from attrdict import AttrDict

import tomcatmanager as tm
from tests.mock_server80 import start_mock_server80

###
#
# add command line options
#
###
def pytest_addoption(parser):
    parser.addoption('--url', action='store', default=None,
        help='url: url of tomcat manager to test against instead of mock')
    parser.addoption('--user', action='store', default=None,
        help='user: use to authenticate')
    parser.addoption('--password', action='store', default=None,
        help='password: use to authenticate')
    parser.addoption('--warfile', action='store', default=None,
        help='warfile: path to deployable war file on the tomcat server')
    parser.addoption('--contextfile', action='store', default=None,
        help='contextfile: path to context.xml file on the tomcat server')


# use a fixture to return a class with a bunch
# of assertion helper methods
@pytest.fixture
def assert_tomcatresponse():
    """
    Assertions for every command that should complete successfully.
    """
    class AssertResponse():
        def success(self, r):
            """Assertions on TomcatResponse for calls that should be successful."""
            assert r.status_code == tm.status_codes.ok, 'message from server: "{}"'.format(r.status_message)
            assert r.status_message != None
            assert r.status_message
            r.raise_for_status()
        def failure(self, r):
            """Assertions on TomcatResponse for calls that should fail."""
            assert r.status_code == tm.status_codes.fail
            with pytest.raises(tm.TomcatError):
                r.raise_for_status()
        def info(self, r):
            """Assertions on TomcatResponse for info-type commands that should be successful."""
            self.success(r)
            assert r.result != None
            assert r.result        
    return AssertResponse()

###
#
# fixtures for testing TomcatManager()
#
###
@pytest.fixture
def tomcat_manager_server(request):
    """start a local http server which provides a similar interface to a real Tomcat Manager app"""
    url = request.config.getoption('--url')
    if url:
        # use the server info specified on the command line
        tms = AttrDict()
        tms.url = url
        tms.user = request.config.getoption('--user')
        tms.password = request.config.getoption('--password')
        tms.warfile = request.config.getoption('--warfile')
        tms.contextfile = request.config.getoption('--contextfile')
        return tms
    else:
        # go start up a fake server
        return start_mock_server80()

@pytest.fixture
def tomcat(tomcat_manager_server):
    tomcat = tm.TomcatManager()
    tomcat.connect(
        tomcat_manager_server.url,
        tomcat_manager_server.user,
        tomcat_manager_server.password
    )
    return tomcat

@pytest.fixture
def localwar_file():
    """return the path to a valid war file"""
    return os.path.dirname(__file__) + '/tests/war/sample.war'

@pytest.fixture
def safe_path():
    """a safe path we can deploy apps to"""
    return '/tomcat-manager-test-app'

@pytest.fixture
def server_info():
    return """Tomcat Version: Apache Tomcat/8.0.32 (Ubuntu)
OS Name: Linux
OS Version: 4.4.0-89-generic
OS Architecture: amd64
JVM Version: 1.8.0_131-8u131-b11-2ubuntu1.16.04.3-b11
JVM Vendor: Oracle Corporation
"""
