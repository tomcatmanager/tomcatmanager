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

import pytest

import tomcatmanager as tm


###
#
# helper functions and fixtures
#
###
def get_itm(tms):
    """
    Using this as a fixture with capsys breaks capsys. So we use a function.
    """
    itm = tm.InteractiveTomcatManager(loadconfig=False)
    itm.onecmd_plus_hooks(tms.connect_command)
    return itm


@pytest.fixture
def itm_nc():
    """Don't allow it to load a config file"""
    itm = tm.InteractiveTomcatManager(loadconfig=False)
    return itm


###
#
# test informational commands
#
###
NOARGS_INFO_COMMANDS = [
    "serverinfo",
    "status",
    "vminfo",
    "sslconnectorciphers",
    "sslconnectorcerts",
    "sslconnectortrustedcerts",
    "threaddump",
    "findleakers",
]


@pytest.mark.parametrize("cmdname", NOARGS_INFO_COMMANDS)
def test_info_commands_noargs(tomcat_manager_server, cmdname):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.EXIT_SUCCESS
    itm.onecmd_plus_hooks(f"{cmdname} argument")
    assert itm.exit_code == itm.EXIT_USAGE


def test_serverinfo(tomcat_manager_server, capsys):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.EXIT_ERROR
    itm.onecmd_plus_hooks("serverinfo")
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert "Tomcat Version: " in out
    assert "JVM Version: " in out


def test_status(tomcat_manager_server, capsys):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.EXIT_ERROR
    itm.onecmd_plus_hooks("status")
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert "</status>" in out
    assert "</jvm>" in out
    assert "</connector>" in out


def test_status_no_spinner(tomcat_manager_server, capsys):
    # this is really to test no activity spinner, not status,
    # but we gotta test it with something
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.EXIT_ERROR
    itm.status_animation = None
    itm.quiet = False
    itm.onecmd_plus_hooks("status")
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert "</status>" in out
    assert "</jvm>" in out
    assert "</connector>" in out


def test_vminfo(tomcat_manager_server, capsys):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.EXIT_ERROR
    itm.onecmd_plus_hooks("vminfo")
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert "Runtime information:" in out
    assert "architecture:" in out
    assert "System properties:" in out


def test_sslconnectorciphers(tomcat_manager_server, capsys):
    itm = get_itm(tomcat_manager_server)
    itm.onecmd_plus_hooks("sslconnectorciphers")
    out, err = capsys.readouterr()
    if "command not implemented by server" in err:
        # the particular version of the server we are testing against
        # doesn't support this command. Silently skip
        assert itm.exit_code == itm.EXIT_ERROR
    else:
        assert itm.exit_code == itm.EXIT_SUCCESS
        assert "Connector" in out
        assert "SSL" in out


def test_sslconnectorcerts(tomcat_manager_server, capsys):
    itm = get_itm(tomcat_manager_server)
    itm.onecmd_plus_hooks("sslconnectorcerts")
    out, err = capsys.readouterr()
    if "command not implemented by server" in err:
        # the particular version of the server we are testing against
        # doesn't support this command. Silently skip
        assert itm.exit_code == itm.EXIT_ERROR
    else:
        assert itm.exit_code == itm.EXIT_SUCCESS
        assert "Connector" in out
        assert "SSL" in out


def test_sslconnectortrustedcerts(tomcat_manager_server, capsys):
    itm = get_itm(tomcat_manager_server)
    itm.onecmd_plus_hooks("sslconnectortrustedcerts")
    out, err = capsys.readouterr()
    if "command not implemented by server" in err:
        # the particular version of the server we are testing against
        # doesn't support this command. Silently skip
        assert itm.exit_code == itm.EXIT_ERROR
    else:
        assert itm.exit_code == itm.EXIT_SUCCESS
        assert "Connector" in out
        assert "SSL" in out


def test_sslreload(tomcat_manager_server, capsys):
    itm = get_itm(tomcat_manager_server)
    itm.onecmd_plus_hooks("sslreload")
    out, err = capsys.readouterr()
    if "command not implemented by server" in err:
        # the particular version of the server we are testing against
        # doesn't support this command
        assert itm.exit_code == itm.EXIT_ERROR
    else:
        # check for something in both out and err, if the server can't
        # reload the SSL/TLS certificates, the output will be in err
        # when testing against a real tomcat server we don't know
        # whether they will successfully reload or not
        # we don't check itm.exit_code here either for the same reason
        assert "load" in out or "load" in err
        assert "TLS" in out or "TLS" in err


def test_sslreload_host(tomcat_manager_server, capsys):
    itm = get_itm(tomcat_manager_server)
    itm.onecmd_plus_hooks("sslreload www.example.com")
    out, err = capsys.readouterr()
    if "command not implemented by server" in err:
        # the particular version of the server we are testing against
        # doesn't support this command. Silently skip
        assert itm.exit_code == itm.EXIT_ERROR
    else:
        # check for something in both out and err, if the server can't
        # reload the SSL/TLS certificates, the output will be in err
        # when testing against a real tomcat server we don't know
        # whether they will successfully reload or not
        # we don't check itm.exit_code here either for the same reason
        assert "load" in out or "load" in err
        assert "TLS" in out or "TLS" in err
        assert "www.example.com" in out or "www.example.com" in err


def test_notimplemented(tomcat_manager_server, capsys, mocker):
    # if the server doesn't implement a command, make sure
    # we get the error message
    connect_mock = mocker.patch("tomcatmanager.TomcatManager.list")
    connect_mock.side_effect = tm.TomcatNotImplementedError
    itm = get_itm(tomcat_manager_server)
    itm.onecmd_plus_hooks("list")
    _, err = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_ERROR
    assert "command not implemented by server" in err


def test_threaddump(tomcat_manager_server, capsys):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.EXIT_ERROR
    itm.onecmd_plus_hooks("threaddump")
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert "java.lang.Thread.State" in out


def test_resources(tomcat_manager_server, itm_nc, capsys):
    itm_nc.exit_code = itm_nc.EXIT_ERROR
    itm_nc.debug = False
    itm_nc.quiet = True
    itm_nc.onecmd_plus_hooks(tomcat_manager_server.connect_command)
    itm_nc.onecmd_plus_hooks("resources")
    out, _ = capsys.readouterr()
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS
    assert "UserDatabase: " in out


def test_resources_class_name(tomcat_manager_server, itm_nc, capsys):
    itm_nc.exit_code = itm_nc.EXIT_SUCCESS
    itm_nc.debug = False
    itm_nc.quiet = True
    itm_nc.onecmd_plus_hooks(tomcat_manager_server.connect_command)
    # this class has to be hand coded in the mock server
    itm_nc.onecmd_plus_hooks("resources com.example.Nothing")
    out, err = capsys.readouterr()
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR
    assert not out.strip()


def test_findleakers(tomcat_manager_server):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.EXIT_ERROR
    itm.onecmd_plus_hooks("findleakers")
    assert itm.exit_code == itm.EXIT_SUCCESS
