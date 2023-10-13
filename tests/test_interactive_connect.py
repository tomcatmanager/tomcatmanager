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
# pylint: disable=protected-access, missing-function-docstring, too-many-lines
# pylint: disable=missing-module-docstring, unused-variable, redefined-outer-name

from unittest import mock
import uuid

import pytest
import requests

import tomcatmanager as tm


###
#
# helper functions and fixtures
#
###
def assert_connected_to(itm, url, capsys):
    itm.onecmd_plus_hooks("which")
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert url in out


###
#
# test connect, which, and disconnect commands
#
###
def test_connect(tomcat_manager_server, capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks(tomcat_manager_server.connect_command)
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert_connected_to(itm, tomcat_manager_server.url, capsys)


def test_connect_noparams(capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks("connect")
    out, err = capsys.readouterr()
    assert out
    assert not err
    assert itm.exit_code == itm.EXIT_USAGE


def test_connect_noverify(tomcat_manager_server, mocker):
    itm = tm.InteractiveTomcatManager()
    get_mock = mocker.patch("requests.get")
    itm.onecmd_plus_hooks(tomcat_manager_server.connect_command + " --noverify")
    url = tomcat_manager_server.url + "/text/serverinfo"
    get_mock.assert_called_once_with(
        url,
        auth=(tomcat_manager_server.user, tomcat_manager_server.password),
        params=None,
        timeout=itm.timeout,
        verify=False,
        cert=None,
    )


def test_connect_cacert(tomcat_manager_server, mocker):
    itm = tm.InteractiveTomcatManager()
    get_mock = mocker.patch("requests.get")
    itm.onecmd_plus_hooks(tomcat_manager_server.connect_command + " --cacert /tmp/ca")
    url = tomcat_manager_server.url + "/text/serverinfo"
    get_mock.assert_called_once_with(
        url,
        auth=(tomcat_manager_server.user, tomcat_manager_server.password),
        params=None,
        timeout=itm.timeout,
        verify="/tmp/ca",
        cert=None,
    )


def test_connect_cacert_noverify(tomcat_manager_server, mocker):
    itm = tm.InteractiveTomcatManager()
    get_mock = mocker.patch("requests.get")
    cmd = tomcat_manager_server.connect_command + " --cacert /tmp/ca --noverify"
    itm.onecmd_plus_hooks(cmd)
    url = tomcat_manager_server.url + "/text/serverinfo"
    get_mock.assert_called_once_with(
        url,
        auth=(tomcat_manager_server.user, tomcat_manager_server.password),
        params=None,
        timeout=itm.timeout,
        verify=False,
        cert=None,
    )


def test_connect_cert(tomcat_manager_server, mocker):
    itm = tm.InteractiveTomcatManager()
    get_mock = mocker.patch("requests.get")
    itm.onecmd_plus_hooks(tomcat_manager_server.connect_command + " --cert /tmp/cert")
    url = tomcat_manager_server.url + "/text/serverinfo"
    get_mock.assert_called_once_with(
        url,
        auth=(tomcat_manager_server.user, tomcat_manager_server.password),
        params=None,
        timeout=itm.timeout,
        verify=True,
        cert="/tmp/cert",
    )


def test_connect_key_cert(tomcat_manager_server, mocker):
    itm = tm.InteractiveTomcatManager()
    get_mock = mocker.patch("requests.get")
    cmd = tomcat_manager_server.connect_command + " --cert /tmp/cert --key /tmp/key"
    itm.onecmd_plus_hooks(cmd)
    url = tomcat_manager_server.url + "/text/serverinfo"
    get_mock.assert_called_once_with(
        url,
        auth=(tomcat_manager_server.user, tomcat_manager_server.password),
        params=None,
        timeout=itm.timeout,
        verify=True,
        cert=("/tmp/cert", "/tmp/key"),
    )


def test_connect_fail_debug(tomcat_manager_server, mocker):
    itm = tm.InteractiveTomcatManager()
    itm.debug = True
    mock_ok = mocker.patch(
        "tomcatmanager.models.TomcatManagerResponse.ok",
        new_callable=mock.PropertyMock,
    )
    mock_ok.return_value = False
    raise_mock = mocker.patch(
        "tomcatmanager.models.TomcatManagerResponse.raise_for_status"
    )
    raise_mock.side_effect = tm.TomcatError()
    itm.onecmd_plus_hooks(tomcat_manager_server.connect_command)
    assert itm.exit_code == itm.EXIT_ERROR


# pylint: disable=too-few-public-methods
class MockResponse:
    """Simple class to help mock.patch"""

    def __init__(self, code):
        self.status_code = code


FAIL_MESSAGES = [
    (requests.codes.ok, "tomcat manager not found"),
    (requests.codes.not_found, "tomcat manager not found"),
    (requests.codes.server_error, "http error"),
]


# pylint: disable=too-many-arguments
@pytest.mark.parametrize("code, errmsg", FAIL_MESSAGES)
def test_connect_fail_ok(tomcat_manager_server, itm, mocker, code, errmsg, capsys):
    itm.debug = False
    itm.quiet = True
    mock_ok = mocker.patch(
        "tomcatmanager.models.TomcatManagerResponse.response",
        new_callable=mock.PropertyMock,
    )
    qmr = MockResponse(code)
    mock_ok.return_value = qmr

    itm.onecmd_plus_hooks(tomcat_manager_server.connect_command)
    out, err = capsys.readouterr()
    assert not out.strip()
    assert errmsg in err
    assert itm.exit_code == itm.EXIT_ERROR


def test_connect_fail_not_found(tomcat_manager_server, itm, mocker, capsys):
    itm.debug = False
    itm.quiet = True
    mock_ok = mocker.patch(
        "tomcatmanager.models.TomcatManagerResponse.response",
        new_callable=mock.PropertyMock,
    )
    qmr = MockResponse(requests.codes.not_found)
    mock_ok.return_value = qmr

    itm.onecmd_plus_hooks(tomcat_manager_server.connect_command)
    out, err = capsys.readouterr()
    assert not out.strip()
    assert "tomcat manager not found" in err
    assert itm.exit_code == itm.EXIT_ERROR


def test_connect_fail_other(tomcat_manager_server, itm, mocker, capsys):
    itm.debug = False
    itm.quiet = True
    mock_ok = mocker.patch(
        "tomcatmanager.models.TomcatManagerResponse.response",
        new_callable=mock.PropertyMock,
    )
    qmr = MockResponse(requests.codes.server_error)
    mock_ok.return_value = qmr

    itm.onecmd_plus_hooks(tomcat_manager_server.connect_command)
    out, err = capsys.readouterr()
    assert not out.strip()
    assert "http error" in err
    assert itm.exit_code == itm.EXIT_ERROR


def test_connect_password_prompt(tomcat_manager_server, capsys, mocker):
    itm = tm.InteractiveTomcatManager()
    mock_getpass = mocker.patch("getpass.getpass")
    mock_getpass.return_value = tomcat_manager_server.password
    # this should call getpass.getpass, which is now mocked to return the password
    cmdline = f"connect {tomcat_manager_server.url} {tomcat_manager_server.user}"
    itm.onecmd_plus_hooks(cmdline)
    # make sure it got called
    assert mock_getpass.call_count == 1
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert_connected_to(itm, tomcat_manager_server.url, capsys)


def test_connect_config(tomcat_manager_server, itm_with_config, capsys):
    host_name = str(uuid.uuid1())

    config_string = f"""
        [{host_name}]
        url = "{tomcat_manager_server.url}"
        user = "{tomcat_manager_server.user}"
        password = "{tomcat_manager_server.password}"
        """
    itm = itm_with_config(config_string)
    cmdline = f"connect {host_name}"
    itm.onecmd_plus_hooks(cmdline)
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert_connected_to(itm, tomcat_manager_server.url, capsys)


def test_connect_config_user_override(tomcat_manager_server, itm_with_config, mocker):
    host_name = str(uuid.uuid1())
    config_string = f"""
        [{host_name}]
        url = "{tomcat_manager_server.url}"
        user = "{tomcat_manager_server.user}"
        password = "{tomcat_manager_server.password}"
        """
    itm = itm_with_config(config_string)
    cmdline = f"connect {host_name} someotheruser"
    get_mock = mocker.patch("requests.get")
    itm.onecmd_plus_hooks(cmdline)
    url = tomcat_manager_server.url + "/text/serverinfo"
    get_mock.assert_called_once_with(
        url,
        auth=("someotheruser", tomcat_manager_server.password),
        params=None,
        timeout=itm.timeout,
        verify=True,
        cert=None,
    )


def test_connect_config_user_password_override(
    tomcat_manager_server, itm_with_config, mocker
):
    host_name = str(uuid.uuid1())
    config_string = f"""
        [{host_name}]
        url = "{tomcat_manager_server.url}"
        user = "{tomcat_manager_server.user}"
        password = "{tomcat_manager_server.password}"
        """
    itm = itm_with_config(config_string)
    cmdline = f"connect {host_name} someotheruser someotherpassword"
    get_mock = mocker.patch("requests.get")
    itm.onecmd_plus_hooks(cmdline)
    url = tomcat_manager_server.url + "/text/serverinfo"
    get_mock.assert_called_once_with(
        url,
        auth=("someotheruser", "someotherpassword"),
        params=None,
        timeout=itm.timeout,
        verify=True,
        cert=None,
    )


def test_connect_config_cert(tomcat_manager_server, itm_with_config, mocker):
    host_name = str(uuid.uuid1())
    config_string = f"""
        [{host_name}]
        url = "{tomcat_manager_server.url}"
        cert = "/tmp/mycert"
        """
    itm = itm_with_config(config_string)
    cmdline = f"connect {host_name}"
    get_mock = mocker.patch("requests.get")
    itm.onecmd_plus_hooks(cmdline)
    url = tomcat_manager_server.url + "/text/serverinfo"
    get_mock.assert_called_once_with(
        url,
        auth=None,
        params=None,
        timeout=itm.timeout,
        verify=True,
        cert="/tmp/mycert",
    )


def test_connect_config_cert_override(tomcat_manager_server, itm_with_config, mocker):
    host_name = str(uuid.uuid1())
    config_string = f"""
        [{host_name}]
        url = "{tomcat_manager_server.url}"
        cert = "/tmp/mycert"
        """
    itm = itm_with_config(config_string)
    cmdline = f"connect {host_name} --cert /tmp/yourcert"
    get_mock = mocker.patch("requests.get")
    itm.onecmd_plus_hooks(cmdline)
    url = tomcat_manager_server.url + "/text/serverinfo"
    get_mock.assert_called_once_with(
        url,
        auth=None,
        params=None,
        timeout=itm.timeout,
        verify=True,
        cert="/tmp/yourcert",
    )


def test_connect_config_cert_key(tomcat_manager_server, itm_with_config, mocker):
    host_name = str(uuid.uuid1())
    config_string = f"""
        [{host_name}]
        url = "{tomcat_manager_server.url}"
        cert = "/tmp/mycert"
        key = "/tmp/mykey"
        """
    itm = itm_with_config(config_string)
    cmdline = f"connect {host_name}"
    get_mock = mocker.patch("requests.get")
    itm.onecmd_plus_hooks(cmdline)
    url = tomcat_manager_server.url + "/text/serverinfo"
    get_mock.assert_called_once_with(
        url,
        auth=None,
        params=None,
        timeout=itm.timeout,
        verify=True,
        cert=("/tmp/mycert", "/tmp/mykey"),
    )


def test_connect_config_cert_key_override(
    tomcat_manager_server, itm_with_config, mocker
):
    host_name = str(uuid.uuid1())
    config_string = f"""
        [{host_name}]
        url = "{tomcat_manager_server.url}"
        cert = "/tmp/mycert"
        key = "/tmp/mykey"
        """
    itm = itm_with_config(config_string)
    cmdline = f"connect {host_name} --cert /tmp/yourcert --key /tmp/yourkey"
    get_mock = mocker.patch("requests.get")
    itm.onecmd_plus_hooks(cmdline)
    url = tomcat_manager_server.url + "/text/serverinfo"
    get_mock.assert_called_once_with(
        url,
        auth=None,
        params=None,
        timeout=itm.timeout,
        verify=True,
        cert=("/tmp/yourcert", "/tmp/yourkey"),
    )


def test_connect_config_cacert(tomcat_manager_server, itm_with_config, mocker):
    host_name = str(uuid.uuid1())
    config_string = f"""
        [{host_name}]
        url = "{tomcat_manager_server.url}"
        user = "{tomcat_manager_server.user}"
        password = "{tomcat_manager_server.password}"
        cacert = "/tmp/cabundle"
        """
    itm = itm_with_config(config_string)
    cmdline = f"connect {host_name}"
    get_mock = mocker.patch("requests.get")
    itm.onecmd_plus_hooks(cmdline)
    url = tomcat_manager_server.url + "/text/serverinfo"
    get_mock.assert_called_once_with(
        url,
        auth=(tomcat_manager_server.user, tomcat_manager_server.password),
        params=None,
        timeout=itm.timeout,
        verify="/tmp/cabundle",
        cert=None,
    )


def test_connect_config_cacert_override(tomcat_manager_server, itm_with_config, mocker):
    host_name = str(uuid.uuid1())
    config_string = f"""
        [{host_name}]
        url = "{tomcat_manager_server.url}"
        user = "{tomcat_manager_server.user}"
        password = "{tomcat_manager_server.password}"
        cacert = "/tmp/cabundle"
        """
    itm = itm_with_config(config_string)
    cmdline = f"connect {host_name} --cacert /tmp/other"
    get_mock = mocker.patch("requests.get")
    itm.onecmd_plus_hooks(cmdline)
    url = tomcat_manager_server.url + "/text/serverinfo"
    get_mock.assert_called_once_with(
        url,
        auth=(tomcat_manager_server.user, tomcat_manager_server.password),
        params=None,
        timeout=itm.timeout,
        verify="/tmp/other",
        cert=None,
    )


def test_connect_config_noverify_override(
    tomcat_manager_server, itm_with_config, mocker
):
    host_nanme = str(uuid.uuid1())
    config_string = f"""
        [{host_nanme}]
        url = "{tomcat_manager_server.url}"
        user = "{tomcat_manager_server.user}"
        password = "{tomcat_manager_server.password}"
        verify = true
        """
    itm = itm_with_config(config_string)
    cmdline = f"connect {host_nanme} --noverify"
    get_mock = mocker.patch("requests.get")
    itm.onecmd_plus_hooks(cmdline)
    url = tomcat_manager_server.url + "/text/serverinfo"
    get_mock.assert_called_once_with(
        url,
        auth=(tomcat_manager_server.user, tomcat_manager_server.password),
        params=None,
        timeout=itm.timeout,
        verify=False,
        cert=None,
    )


def test_connect_config_noverify_override_cacert(
    tomcat_manager_server, itm_with_config, mocker
):
    host_name = str(uuid.uuid1())
    config_string = f"""
        [{host_name}]
        url = "{tomcat_manager_server.url}"
        user = "{tomcat_manager_server.user}"
        password = "{tomcat_manager_server.password}"
        cacert = "/tmp/cabundle"
        """
    itm = itm_with_config(config_string)
    cmdline = f"connect {host_name} --noverify"
    get_mock = mocker.patch("requests.get")
    itm.onecmd_plus_hooks(cmdline)
    url = tomcat_manager_server.url + "/text/serverinfo"
    get_mock.assert_called_once_with(
        url,
        auth=(tomcat_manager_server.user, tomcat_manager_server.password),
        params=None,
        timeout=itm.timeout,
        verify=False,
        cert=None,
    )


def test_connect_config_password_prompt(
    tomcat_manager_server, itm_with_config, capsys, mocker
):
    host_name = str(uuid.uuid1())
    config_string = f"""
        [{host_name}]
        url = "{tomcat_manager_server.url}"
        user = "{tomcat_manager_server.user}"
        """
    itm = itm_with_config(config_string)
    mock_getpass = mocker.patch("getpass.getpass")
    mock_getpass.return_value = tomcat_manager_server.password
    # this will call getpass.getpass, which is now mocked to return the password
    cmdline = f"connect {host_name}"
    itm.onecmd_plus_hooks(cmdline)
    assert mock_getpass.call_count == 1
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert_connected_to(itm, tomcat_manager_server.url, capsys)


def test_connect_with_connection_error(tomcat_manager_server, itm_nc, capsys, mocker):
    connect_mock = mocker.patch("tomcatmanager.TomcatManager.connect")
    connect_mock.side_effect = requests.exceptions.ConnectionError()
    itm_nc.debug = False
    itm_nc.quiet = True
    itm_nc.onecmd_plus_hooks(tomcat_manager_server.connect_command)
    out, err = capsys.readouterr()
    assert not out.strip()
    assert connect_mock.call_count == 1
    assert "connection error" in err
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR


def test_connect_with_connection_error_debug(
    tomcat_manager_server, itm_nc, capsys, mocker
):
    connect_mock = mocker.patch("tomcatmanager.TomcatManager.connect")
    connect_mock.side_effect = requests.exceptions.ConnectionError()
    itm_nc.debug = True
    itm_nc.quiet = True
    itm_nc.onecmd_plus_hooks(tomcat_manager_server.connect_command)
    out, err = capsys.readouterr()
    assert not out.strip()
    assert connect_mock.call_count == 1
    assert "requests.exceptions.ConnectionError" in err
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR


def test_connect_with_timeout(tomcat_manager_server, itm_nc, capsys, mocker):
    connect_mock = mocker.patch("tomcatmanager.TomcatManager.connect")
    connect_mock.side_effect = requests.exceptions.Timeout()
    itm_nc.debug = False
    itm_nc.quiet = True
    itm_nc.onecmd_plus_hooks(tomcat_manager_server.connect_command)
    out, err = capsys.readouterr()
    assert not out.strip()
    assert connect_mock.call_count == 1
    assert "connection timeout" in err
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR


def test_connect_with_timeout_debug(tomcat_manager_server, itm_nc, capsys, mocker):
    connect_mock = mocker.patch("tomcatmanager.TomcatManager.connect")
    connect_mock.side_effect = requests.exceptions.Timeout()
    itm_nc.debug = True
    itm_nc.quiet = True
    itm_nc.onecmd_plus_hooks(tomcat_manager_server.connect_command)
    out, err = capsys.readouterr()
    assert not out.strip()
    assert connect_mock.call_count == 1
    assert "requests.exceptions.Timeout" in err
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR


def test_which(tomcat_manager_server, itm, capsys):
    # force this to ensure `which` sets it to SUCCESS
    itm.exit_code = itm.EXIT_ERROR
    itm.onecmd_plus_hooks("which")
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert tomcat_manager_server.url in out
    assert tomcat_manager_server.user in out


def test_which_cert(itm, capsys, mocker):
    # the mock tomcat server can't authenticate using a certificate
    # so we connect as normal, then mock it so it appears
    # like we authenticated with a certificate
    cert_mock = mocker.patch(
        "tomcatmanager.TomcatManager.cert",
        new_callable=mock.PropertyMock,
    )
    cert_mock.return_value = "/tmp/mycert"
    itm.onecmd_plus_hooks("which")
    out, _ = capsys.readouterr()
    assert "/tmp/mycert" in out


def test_which_cert_key(itm, capsys, mocker):
    # the mock tomcat erver can't authenticate using a certificate
    # so we connect as normal, then mock it so it appears
    # like we authenticated with a certificate
    cert_mock = mocker.patch(
        "tomcatmanager.TomcatManager.cert",
        new_callable=mock.PropertyMock,
    )
    cert_mock.return_value = ("/tmp/mycert", "/tmp/mykey")
    itm.onecmd_plus_hooks("which")
    out, _ = capsys.readouterr()
    assert "/tmp/mykey" in out


def test_disconnect(itm, capsys):
    # force this to ensure `which` sets it to SUCCESS
    itm.exit_code = itm.EXIT_ERROR
    itm.onecmd_plus_hooks("disconnect")
    _, err = capsys.readouterr()
    assert "disconnected" in err
    assert itm.exit_code == itm.EXIT_SUCCESS
    itm.onecmd_plus_hooks("which")
    assert itm.exit_code == itm.EXIT_ERROR


REQUIRES_CONNECTION = [
    "which",
    "deploy local file.war /path",
    "deploy server file.war /path",
    "deploy context context.xml /path",
    "redeploy local file.war /path",
    "redeploy server file.war /path",
    "redeploy context context.xml /path",
    "undeploy /path",
    "start /path",
    "stop /path",
    "reload path",
    "restart /path",
    "sessions /path",
    "expire /path 3600",
    "list",
    "serverinfo",
    "status",
    "vminfo",
    "sslconnectorciphers",
    "sslconnectorcerts",
    "sslconnectortrustedcerts",
    "sslreload",
    "threaddump",
    "resources",
    "findleakers",
]


@pytest.mark.parametrize("command", REQUIRES_CONNECTION)
def test_requires_connection(itm_nc, command, capsys):
    itm_nc.onecmd_plus_hooks(command)
    out, err = capsys.readouterr()
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR
    assert not out
    assert err == "not connected\n"
