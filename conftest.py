#
# -*- coding: utf-8 -*-
# pylint: disable=missing-function-docstring, missing-module-docstring
# pylint: disable=missing-class-docstring, redefined-outer-name

import pathlib
import pytest
from unittest import mock

import requests

import tomcatmanager as tm

from tests.mock_server_10_1 import start_mock_server_10_1
from tests.mock_server_10_0 import start_mock_server_10_0
from tests.mock_server_9_0 import start_mock_server_9_0
from tests.mock_server_8_5 import start_mock_server_8_5


###
#
# helper classes
#
###
# pylint: disable=too-few-public-methods
class TomcatServer:
    def __init__(self):
        self.url = None
        self.user = None
        self.password = None
        self.cert = None
        self.verify = True
        self.warfile = None
        self.contextfile = None
        self.connect_command = None


###
#
# add command line options
#
###
def pytest_addoption(parser):
    parser.addoption(
        "--mocktomcat",
        action="store",
        default=tm.TomcatMajorMinor.highest_supported().value,
        choices=list(map(lambda v: v.value, tm.TomcatMajorMinor.supported())),
        help="test against a specific mock version of Tomcat",
    )
    parser.addoption(
        "--url",
        action="store",
        help="url of tomcat manager to test against instead of mock server",
    )
    parser.addoption("--user", action="store", help="use to authenticate at url")
    parser.addoption("--password", action="store", help="use to authenticate at url")
    parser.addoption(
        "--cert",
        action="store",
        help="certificate for client side authentication",
    )
    parser.addoption(
        "--key",
        action="store",
        help="private key file for client side authentication",
    )
    parser.addoption(
        "--warfile",
        action="store",
        help="path to deployable war file on the tomcat server",
    )
    parser.addoption(
        "--contextfile",
        action="store",
        help="path to context.xml file on the tomcat server",
    )
    parser.addoption(
        "--cacert",
        action="store",
        help="path to certificate authority bundle or directory",
    )
    parser.addoption(
        "--noverify",
        # store_true makes the default False, aka default is to verify
        # server certificates
        action="store_true",
        help="don't validate server SSL certificates",
    )


###
#
# fixtures
#
###


# use a fixture to return a class with a bunch
# of assertion helper methods
@pytest.fixture
def assert_tomcatresponse():
    """
    Assertions for every command that should complete successfully.
    """

    class AssertResponse:
        def success(self, r):
            """Assertions on TomcatResponse for calls that should be successful."""
            assert (
                r.status_code == tm.StatusCode.OK
            ), f'message from server: "{r.status_message}"'
            assert r.status_message
            r.raise_for_status()

        def failure(self, r):
            """Assertions on TomcatResponse for calls that should fail."""
            assert r.status_code == tm.StatusCode.FAIL
            with pytest.raises(tm.TomcatError):
                r.raise_for_status()

        def info(self, r):
            """Assertions on TomcatResponse for info-type commands that should be successful."""
            self.success(r)
            assert r.result

    return AssertResponse()


@pytest.fixture(scope="session")
def tomcat_manager_server(request):
    """start a local http server which provides a similar interface to a
    real Tomcat Manager app"""
    url = request.config.getoption("--url")
    tms = TomcatServer()
    if url:
        # use the server info specified on the command line
        tms.url = url
        tms.user = request.config.getoption("--user")
        tms.password = request.config.getoption("--password")
        cert = request.config.getoption("--cert")
        key = request.config.getoption("--key")
        if cert and key:
            cert = (cert, key)
        tms.cert = cert
        cacert = request.config.getoption("--cacert")
        # the command line option is negative, so this flips it
        verify = not request.config.getoption("--noverify")
        if verify and cacert:
            tms.verify = cacert
        else:
            tms.verify = verify
        tms.warfile = request.config.getoption("--warfile")
        tms.contextfile = request.config.getoption("--contextfile")
        tms.connect_command = f"connect {tms.url} {tms.user} {tms.password}"
        yield tms
    else:
        # we don't have a url on the command line, go start up a fake server
        mockver = request.config.getoption("--mocktomcat")
        if mockver == tm.TomcatMajorMinor.V10_1.value:
            (mock_server, tms) = start_mock_server_10_1(tms)
        elif mockver == tm.TomcatMajorMinor.V10_0.value:
            (mock_server, tms) = start_mock_server_10_0(tms)
        elif mockver == tm.TomcatMajorMinor.V9_0.value:
            (mock_server, tms) = start_mock_server_9_0(tms)
        elif mockver == tm.TomcatMajorMinor.V8_5.value:
            (mock_server, tms) = start_mock_server_8_5(tms)
        else:
            raise NotImplementedError()

        yield tms
        mock_server.shutdown()


@pytest.fixture
def tomcat(tomcat_manager_server):
    tmcat = tm.TomcatManager()
    tmcat.connect(
        tomcat_manager_server.url,
        tomcat_manager_server.user,
        tomcat_manager_server.password,
        cert=tomcat_manager_server.cert,
    )
    return tmcat


@pytest.fixture
def itm_nc():
    """InteractiveTomcatManager with no config file loaded
    and not connected to a server

    nc = not connected
    nc = no config

    Unless we have a good reason to do otherwise, we never want
    our tests to load whatever config file the person running
    the tests happens to have
    """
    return tm.InteractiveTomcatManager(loadconfig=False)


@pytest.fixture
def itm(itm_nc, tomcat_manager_server):
    """InteractiveTomcatManager instance with no config file loaded
    and connected to a tomcat server

    This has the shortest name because it's the test fixture used
    most frequently
    """
    itm_nc.onecmd_plus_hooks(tomcat_manager_server.connect_command)
    return itm_nc


@pytest.fixture
def itm_with_config(mocker, tmp_path):
    # make this fixture return a function we can call
    # the config string may need to be dynamically created in a test
    # so we can't use @pytest.mark to attach the data to the test
    #
    # use it like this:
    #
    # def test_mytest(itm_with_config):
    #     config_string = f"""
    #         [settings]
    #         prompt = "$ "
    #         """
    #     itm = itm_with_config(config_string)
    #
    # itm will now contain an InteractiveTomcatManager instance that has loaded
    # the configuration in `config_string`
    #
    def func(config_string):
        # prevent notification of conversion from old to new format
        mocker.patch(
            "tomcatmanager.InteractiveTomcatManager.config_file_old",
            new_callable=mock.PropertyMock,
            return_value=None,
        )

        # create an interactive tomcat manager object
        itm = tm.InteractiveTomcatManager(loadconfig=False)
        # write the passed string to a temp file
        configfile = tmp_path / "tomcat-manager.toml"
        with open(configfile, "w", encoding="utf-8") as fobj:
            fobj.write(config_string)

        # itm aleady tried to load a config file, which it may or may not
        # have found, depending on if you have one or not
        # we are now going to patch up the config_file to point to
        # a known file, and the reload the config from that
        mocker.patch(
            "tomcatmanager.InteractiveTomcatManager.config_file",
            new_callable=mock.PropertyMock,
            return_value=configfile,
        )
        # this has to be inside the context manager for tmpdir because
        # the config file will get deleted when the context manager is
        # no longer in scope
        itm.load_config()
        # this just verifies that our patch worked
        assert itm.config_file == configfile
        return itm

    return func


@pytest.fixture
def localwar_file():
    """return the path to a valid war file"""
    projdir = pathlib.Path(__file__).parent
    return projdir / "tests" / "war" / "sample.war"


@pytest.fixture
def safe_path():
    """a safe path we can deploy apps to in a tomcat server"""
    return "/tomcat-manager-test-app"


@pytest.fixture
def response_with():
    # make this fixture return a function we can call to create
    # a requests.Response object suitable for returning from
    # mocked requests.get() calls
    #
    # use it like this:
    #
    # def test_mytest(response_with):
    #     response_str = f"""
    #         [settings]
    #         prompt = "$ "
    #         """
    #     response = response_with(200, response_string)
    #
    # response will now contain a requests.Response() instance that has
    # a status_code of 200 and a .text attribute containing response_string
    #
    def func(status_code, response_str):
        """make a requests.Response object containing the passed string content"""
        resp = requests.Response()
        resp.status_code = status_code
        resp.encoding = "utf-8"
        resp._content = bytes(response_str, resp.encoding)
        return resp

    return func
