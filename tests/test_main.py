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


def test_main_config_file(mocker, capsys):
    mock_cmdloop = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.cmdloop", autospec=True
    )

    cmdline = "--config-file"
    argv = cmdline.split(" ")
    exit_code = main(argv)
    out, _ = capsys.readouterr()
    out = out.splitlines()
    assert exit_code == 0
    # we aren't going to test what is output, that's tested elsewhere
    # we just need to make sure we got something, and we didn't enter
    # the command loop
    assert out[0]
    assert mock_cmdloop.call_count == 0


def test_main_theme_dir(mocker, capsys):
    mock_cmdloop = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.cmdloop", autospec=True
    )

    cmdline = "--theme-dir"
    argv = cmdline.split(" ")
    exit_code = main(argv)
    out, _ = capsys.readouterr()
    out = out.splitlines()
    assert exit_code == 0
    # we aren't going to test what is output, that's tested elsewhere
    # we just need to make sure we got something, and we didn't enter
    # the command loop
    assert out[0]
    assert mock_cmdloop.call_count == 0


def test_main_noargs(mocker):
    mock_cmdloop = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.cmdloop", autospec=True
    )
    argv = []
    main(argv)
    assert mock_cmdloop.call_count == 1


def test_main_sys_argv(tomcat_manager_server, capsys, mocker, monkeypatch):
    # don't let it load a config file
    mocker.patch("tomcatmanager.InteractiveTomcatManager.load_config", autospec=True)

    # hack up sys.argv
    monkeypatch.setattr(
        "sys.argv",
        [
            "tomcat-manager",
            "--noconfig",
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
    out = out.strip().splitlines()
    assert exit_code == 0
    assert "Path" in out[0]
    assert "Sessions" in out[0]
    assert "connected to" in err


def test_main_user_password_url_command(tomcat_manager_server, mocker, capsys):
    # don't let it load a config file
    loader = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.load_config", autospec=True
    )

    cmdline = (
        f"-u {tomcat_manager_server.user}"
        f" -p {tomcat_manager_server.password} {tomcat_manager_server.url} list"
    )
    argv = cmdline.split(" ")
    exit_code = main(argv)
    out, err = capsys.readouterr()
    out = out.splitlines()

    # make sure it tried to load the config file
    assert loader.called
    assert exit_code == 0
    assert "Path" in out[0]
    assert "Sessions" in out[0]
    assert "connected to" in err


def test_main_quiet(tomcat_manager_server, mocker, capsys):
    # don't let it load a config file
    mocker.patch("tomcatmanager.InteractiveTomcatManager.load_config", autospec=True)

    cmdline = (
        f"-q -u {tomcat_manager_server.user}"
        f" -p {tomcat_manager_server.password} {tomcat_manager_server.url} list"
    )
    argv = cmdline.split(" ")
    exit_code = main(argv)
    out, err = capsys.readouterr()
    out = out.splitlines()
    assert exit_code == 0
    assert "Path" in out[0]
    assert not err.strip()


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


def test_main_noconfig(tomcat_manager_server, capsys, mocker, monkeypatch):
    # mock the config loader so we can check if it was called
    loader = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.load_config", autospec=True
    )

    # hack up sys.argv
    monkeypatch.setattr(
        "sys.argv",
        [
            "tomcat-manager",
            "--noconfig",
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

    assert not loader.called
    assert exit_code == 0
    assert "Path" in out[0]
    assert "Sessions" in out[0]
    assert "connected to" in err


def test_main_debug(tomcat_manager_server, mocker, capsys):
    # don't let it load a config file
    mocker.patch("tomcatmanager.InteractiveTomcatManager.load_config", autospec=True)

    cmdline = (
        f"-d -u {tomcat_manager_server.user}"
        f" -p {tomcat_manager_server.password} {tomcat_manager_server.url} list"
    )
    argv = cmdline.split(" ")
    exit_code = main(argv)
    out, err = capsys.readouterr()
    out = out.splitlines()
    assert exit_code == 0
    assert err
    assert "Path" in out[0]
    assert "Sessions" in out[0]


def test_main_version_with_others(tomcat_manager_server, mocker, capsys):
    # don't let it load a config file
    mocker.patch("tomcatmanager.InteractiveTomcatManager.load_config", autospec=True)

    cmdline = (
        f"-v -q -u {tomcat_manager_server.user}"
        f" -p {tomcat_manager_server.password} {tomcat_manager_server.url} list"
    )
    argv = cmdline.split(" ")
    with pytest.raises(SystemExit) as exit_e:
        main(argv)
    out, err = capsys.readouterr()
    out = out.splitlines()
    assert exit_e.value.code == 0
    assert out[0] == tm.VERSION_STRING
    assert not err


def test_main_stdin(tomcat_manager_server, mocker, capsys):
    # don't let it load a config file
    mocker.patch("tomcatmanager.InteractiveTomcatManager.load_config", autospec=True)

    inio = io.StringIO("list\n")
    stdin = sys.stdin
    cmdline = (
        f"-u {tomcat_manager_server.user}"
        f" -p {tomcat_manager_server.password} {tomcat_manager_server.url}"
    )
    argv = cmdline.split(" ")
    try:
        sys.stdin = inio
        exit_code = main(argv)
    finally:
        sys.stdin = stdin

    out, err = capsys.readouterr()
    out = out.splitlines()
    assert exit_code == 0
    assert "Path" in out[0]
    assert "Sessions" in out[0]
    assert "connected to" in err


def test_main_echo(tomcat_manager_server, mocker, capsys):
    # don't let it load a config file
    mocker.patch("tomcatmanager.InteractiveTomcatManager.load_config", autospec=True)

    inio = io.StringIO("list\n")
    stdin = sys.stdin
    cmdline = (
        f"-e -u {tomcat_manager_server.user}"
        f" -p {tomcat_manager_server.password} {tomcat_manager_server.url}"
    )
    argv = cmdline.split(" ")
    try:
        sys.stdin = inio
        exit_code = main(argv)
    finally:
        sys.stdin = stdin

    out, err = capsys.readouterr()
    out = out.splitlines()
    assert exit_code == 0
    assert " list" in out[0]
    assert "Path" in out[1]
    assert "Sessions" in out[1]
    assert "connected to" in err


def test_main_status_to_stdout(tomcat_manager_server, mocker, capsys):
    # don't let it load a config file
    mocker.patch("tomcatmanager.InteractiveTomcatManager.load_config", autospec=True)

    cmdline = (
        f"-s -u {tomcat_manager_server.user}"
        f" -p {tomcat_manager_server.password} {tomcat_manager_server.url}"
        f" list"
    )
    argv = cmdline.split(" ")
    exit_code = main(argv)
    out, _ = capsys.readouterr()
    out = out.splitlines()
    assert exit_code == 0
    assert "connecting" in out[0]
    assert "connected to" in out[1]
    assert "tomcat version" in out[2]
    assert "listing" in out[3]
    # out[4] is a status message from the server
    assert "Path" in out[5]
    assert "Sessions" in out[5]


def test_main_timeout(tomcat_manager_server, mocker, capsys):
    # don't let it load a config file
    mocker.patch("tomcatmanager.InteractiveTomcatManager.load_config", autospec=True)

    cmdline = (
        f"-t 7.8 -u {tomcat_manager_server.user}"
        f" -p {tomcat_manager_server.password} {tomcat_manager_server.url}"
        f" settings timeout"
    )
    argv = cmdline.split(" ")
    exit_code = main(argv)
    out, _ = capsys.readouterr()
    out = out.splitlines()
    assert exit_code == 0
    assert "timeout = 7.8" in out[0]


def test_main_timeout_zero(tomcat_manager_server, mocker, capsys):
    # don't let it load a config file
    mocker.patch("tomcatmanager.InteractiveTomcatManager.load_config", autospec=True)

    cmdline = (
        f"-t 0 -u {tomcat_manager_server.user}"
        f" -p {tomcat_manager_server.password} {tomcat_manager_server.url}"
        f" settings timeout"
    )
    argv = cmdline.split(" ")
    exit_code = main(argv)
    out, _ = capsys.readouterr()
    out = out.splitlines()
    assert exit_code == 0
    assert "timeout = 0.0" in out[0]


def test_main_theme_command_line(tomcat_manager_server, mocker, monkeypatch, capsys):
    # don't let it load a config file
    mocker.patch("tomcatmanager.InteractiveTomcatManager.load_config", autospec=True)
    # make sure there is an environment variable, which the command line should
    # override
    monkeypatch.setenv("TOMCATMANAGER_THEME", "default-dark")

    cmdline = (
        f"-m default-light -u {tomcat_manager_server.user}"
        f" -p {tomcat_manager_server.password} {tomcat_manager_server.url}"
        f" settings theme"
    )
    argv = cmdline.split(" ")
    exit_code = main(argv)
    out, _ = capsys.readouterr()
    out = out.splitlines()
    assert exit_code == 0
    assert 'theme = "default-light"' in out[0]


def test_main_theme_env(tomcat_manager_server, mocker, monkeypatch, capsys):
    # don't let it load a config file
    mocker.patch("tomcatmanager.InteractiveTomcatManager.load_config", autospec=True)
    # set our desired theme in the environment variable
    monkeypatch.setenv("TOMCATMANAGER_THEME", "default-dark")

    cmdline = (
        f"-u {tomcat_manager_server.user}"
        f" -p {tomcat_manager_server.password} {tomcat_manager_server.url}"
        f" settings theme"
    )
    argv = cmdline.split(" ")
    exit_code = main(argv)
    out, _ = capsys.readouterr()
    out = out.splitlines()
    assert exit_code == 0
    assert 'theme = "default-dark"' in out[0]
