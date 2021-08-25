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
# pylint: disable=protected-access, missing-function-docstring
# pylint: disable=missing-module-docstring, unused-variable

import io
import sys

import pytest

import tomcatmanager as tm
from tomcatmanager.__main__ import main


def test_main_noargs(mocker):
    mock_cmdloop = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.cmdloop", autospec=True
    )
    argv = []
    main(argv)
    assert mock_cmdloop.call_count == 1


def test_main_sys_argv(tomcat_manager_server, capsys, monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "tomcat-manager",
            "-u",
            tomcat_manager_server.user,
            "-p",
            tomcat_manager_server.password,
            tomcat_manager_server.url,
            "list",
        ],
    )

    exit_code = main()
    out, err = capsys.readouterr()
    out = out.splitlines()
    err = err.splitlines()
    assert exit_code == 0
    assert "Path" in out[0]
    assert "Sessions" in out[0]
    assert "--connected to" in err[0]


def test_main_user_password_url_command(tomcat_manager_server, capsys):
    cmdline = "-u {} -p {} {} list".format(
        tomcat_manager_server.user,
        tomcat_manager_server.password,
        tomcat_manager_server.url,
    )
    argv = cmdline.split(" ")
    exit_code = main(argv)
    out, err = capsys.readouterr()
    out = out.splitlines()
    err = err.splitlines()
    assert exit_code == 0
    assert "Path" in out[0]
    assert "Sessions" in out[0]
    assert "--connected to" in err[0]


def test_main_quiet(tomcat_manager_server, capsys):
    cmdline = "-q -u {} -p {} {} list".format(
        tomcat_manager_server.user,
        tomcat_manager_server.password,
        tomcat_manager_server.url,
    )
    argv = cmdline.split(" ")
    exit_code = main(argv)
    out, err = capsys.readouterr()
    out = out.splitlines()
    assert exit_code == 0
    assert "Path" in out[0]
    assert not err


def test_main_help(capsys):
    with pytest.raises(SystemExit) as exit_e:
        main(["--help"])
    out, err = capsys.readouterr()
    out = out.splitlines()
    assert exit_e.value.code == 0
    assert "usage" in out[0]
    assert not err


def test_main_version(capsys):
    with pytest.raises(SystemExit) as exit_e:
        main(["--version"])
    out, err = capsys.readouterr()
    out = out.splitlines()
    assert exit_e.value.code == 0
    assert out[0] == tm.VERSION_STRING
    assert not err


def test_main_debug(tomcat_manager_server, capsys):
    cmdline = "-d -u {} -p {} {} list".format(
        tomcat_manager_server.user,
        tomcat_manager_server.password,
        tomcat_manager_server.url,
    )
    argv = cmdline.split(" ")
    exit_code = main(argv)
    out, err = capsys.readouterr()
    out = out.splitlines()
    assert exit_code == 0
    assert err
    assert "Path" in out[0]
    assert "Sessions" in out[0]


def test_main_version_with_others(tomcat_manager_server, capsys):
    cmdline = "-v -q -u {} -p {} {} list".format(
        tomcat_manager_server.user,
        tomcat_manager_server.password,
        tomcat_manager_server.url,
    )
    argv = cmdline.split(" ")
    with pytest.raises(SystemExit) as exit_e:
        main(argv)
    out, err = capsys.readouterr()
    out = out.splitlines()
    assert exit_e.value.code == 0
    assert out[0] == tm.VERSION_STRING
    assert not err


def test_main_stdin(tomcat_manager_server, capsys):
    inio = io.StringIO("list\n")
    stdin = sys.stdin
    cmdline = "-u {} -p {} {}".format(
        tomcat_manager_server.user,
        tomcat_manager_server.password,
        tomcat_manager_server.url,
    )
    argv = cmdline.split(" ")
    try:
        sys.stdin = inio
        exit_code = main(argv)
    finally:
        sys.stdin = stdin

    out, err = capsys.readouterr()
    out = out.splitlines()
    err = err.splitlines()
    assert exit_code == 0
    assert "Path" in out[0]
    assert "Sessions" in out[0]
    assert "--connected to" in err[0]


def test_main_echo(tomcat_manager_server, capsys):
    inio = io.StringIO("list\n")
    stdin = sys.stdin
    cmdline = "-e -u {} -p {} {}".format(
        tomcat_manager_server.user,
        tomcat_manager_server.password,
        tomcat_manager_server.url,
    )
    argv = cmdline.split(" ")
    try:
        sys.stdin = inio
        exit_code = main(argv)
    finally:
        sys.stdin = stdin

    out, err = capsys.readouterr()
    out = out.splitlines()
    err = err.splitlines()
    assert exit_code == 0
    assert " list" in out[0]
    assert "Path" in out[1]
    assert "Sessions" in out[1]
    assert "--connected to" in err[0]


def test_main_status_to_stdout(tomcat_manager_server, capsys):
    cmdline = "-s -u {} -p {} {} list".format(
        tomcat_manager_server.user,
        tomcat_manager_server.password,
        tomcat_manager_server.url,
    )
    argv = cmdline.split(" ")
    exit_code = main(argv)
    out, _ = capsys.readouterr()
    out = out.splitlines()
    assert exit_code == 0
    assert "--connected to" in out[0]
    assert "--tomcat version" in out[1]
    assert "Path" in out[2]
    assert "Sessions" in out[2]


def test_main_timeout(tomcat_manager_server, capsys):
    cmdline = "-t 7.8 -u {} -p {} {} settings timeout".format(
        tomcat_manager_server.user,
        tomcat_manager_server.password,
        tomcat_manager_server.url,
    )
    argv = cmdline.split(" ")
    exit_code = main(argv)
    out, _ = capsys.readouterr()
    out = out.splitlines()
    assert exit_code == 0
    assert "timeout=7.8" in out[0]


def test_main_timeout_zero(tomcat_manager_server, capsys):
    cmdline = "-t 0 -u {} -p {} {} settings timeout".format(
        tomcat_manager_server.user,
        tomcat_manager_server.password,
        tomcat_manager_server.url,
    )
    argv = cmdline.split(" ")
    exit_code = main(argv)
    out, _ = capsys.readouterr()
    out = out.splitlines()
    assert exit_code == 0
    assert "timeout=0.0" in out[0]
