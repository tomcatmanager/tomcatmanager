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
# misc tests
#
###
def test_notimplemented(itm, capsys, mocker):
    # if the server doesn't implement a command, make sure
    # we get the error message
    connect_mock = mocker.patch("tomcatmanager.TomcatManager.list")
    connect_mock.side_effect = tm.TomcatNotImplementedError
    itm.onecmd_plus_hooks("list")
    _, err = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_ERROR
    assert "command not implemented by server" in err


def test_status_no_spinner(itm, capsys):
    # this is really to test no activity spinner, not status,
    # but we gotta test it with something
    itm.exit_code = itm.EXIT_ERROR
    itm.status_animation = None
    itm.quiet = False
    itm.onecmd_plus_hooks("status")
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert "</status>" in out
    assert "</jvm>" in out
    assert "</connector>" in out


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
def test_info_commands_noargs(itm, cmdname):
    itm.exit_code = itm.EXIT_SUCCESS
    itm.onecmd_plus_hooks(f"{cmdname} argument")
    assert itm.exit_code == itm.EXIT_USAGE


def test_serverinfo(itm, capsys):
    itm.exit_code = itm.EXIT_ERROR
    itm.onecmd_plus_hooks("serverinfo")
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert "Tomcat Version: " in out
    assert "JVM Version: " in out


def test_status(itm, capsys):
    itm.exit_code = itm.EXIT_ERROR
    itm.onecmd_plus_hooks("status")
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert "</status>" in out
    assert "</jvm>" in out
    assert "</connector>" in out


def test_vminfo(itm, capsys):
    itm.exit_code = itm.EXIT_ERROR
    itm.onecmd_plus_hooks("vminfo")
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert "Runtime information:" in out
    assert "architecture:" in out
    assert "System properties:" in out


def test_threaddump(itm, capsys):
    itm.exit_code = itm.EXIT_ERROR
    itm.onecmd_plus_hooks("threaddump")
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert "java.lang.Thread.State" in out


def test_resources(itm, capsys):
    itm.exit_code = itm.EXIT_ERROR
    itm.onecmd_plus_hooks("resources")
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert "UserDatabase: " in out


def test_resources_class_name(itm, capsys):
    itm.exit_code = itm.EXIT_SUCCESS
    # this class has to be hand coded in the mock server
    itm.onecmd_plus_hooks("resources com.example.Nothing")
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_ERROR
    assert not out.strip()


def test_findleakers(itm):
    itm.exit_code = itm.EXIT_ERROR
    itm.onecmd_plus_hooks("findleakers")
    assert itm.exit_code == itm.EXIT_SUCCESS


###
#
# test ssl related commands
#
###
def test_sslconnectorciphers(itm, capsys):
    itm.onecmd_plus_hooks("sslconnectorciphers")
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert "Connector" in out
    assert "SSL" in out


def test_sslconnectorcerts(itm, capsys):
    itm.onecmd_plus_hooks("sslconnectorcerts")
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert "Connector" in out
    assert "SSL" in out


def test_sslconnectortrustedcerts(itm, capsys):
    itm.onecmd_plus_hooks("sslconnectortrustedcerts")
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert "Connector" in out
    assert "SSL" in out


def test_sslreload(itm, capsys):
    itm.onecmd_plus_hooks("sslreload")
    out, err = capsys.readouterr()
    # check for something in both out and err, if the server can't
    # reload the SSL/TLS certificates, the output will be in err
    # when testing against a real tomcat server we don't know
    # whether they will successfully reload or not
    # we don't check itm.exit_code here either for the same reason
    assert "load" in out or "load" in err
    assert "TLS" in out or "TLS" in err


def test_sslreload_host(itm, capsys):
    itm.onecmd_plus_hooks("sslreload www.example.com")
    out, err = capsys.readouterr()
    # check for something in both out and err, if the server can't
    # reload the SSL/TLS certificates, the output will be in err
    # when testing against a real tomcat server we don't know
    # whether they will successfully reload or not
    # we don't check itm.exit_code here either for the same reason
    assert "load" in out or "load" in err
    assert "TLS" in out or "TLS" in err
    assert "www.example.com" in out or "www.example.com" in err
