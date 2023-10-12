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

from unittest import mock

import pytest
import cmd2

import tomcatmanager as tm


VERSION_STRINGS = ["", "-v 42"]


###
#
# deploy, redeploy
#
###
@pytest.mark.parametrize("version", VERSION_STRINGS)
def test_deploy_local(itm, localwar_file, safe_path, version):
    itm.onecmd_plus_hooks(f"redeploy local {version} {localwar_file} {safe_path}")
    assert itm.exit_code == itm.EXIT_SUCCESS

    itm.onecmd_plus_hooks(f"undeploy {version} {safe_path}")
    assert itm.exit_code == itm.EXIT_SUCCESS


@pytest.mark.parametrize("version", VERSION_STRINGS)
def test_redeploy_local(itm, localwar_file, safe_path, version):
    itm.onecmd_plus_hooks(f"deploy local {version} {localwar_file} {safe_path}")
    assert itm.exit_code == itm.EXIT_SUCCESS

    itm.onecmd_plus_hooks(f"redeploy local {version} {localwar_file} {safe_path}")
    assert itm.exit_code == itm.EXIT_SUCCESS

    itm.onecmd_plus_hooks(f"undeploy {version} {safe_path}")
    assert itm.exit_code == itm.EXIT_SUCCESS


@pytest.mark.parametrize("version", VERSION_STRINGS)
def test_deploy_server(itm, tomcat_manager_server, safe_path, version):
    itm.onecmd_plus_hooks(
        f"deploy server {version} {tomcat_manager_server.warfile} {safe_path}"
    )
    assert itm.exit_code == itm.EXIT_SUCCESS

    itm.onecmd_plus_hooks(f"undeploy {version} {safe_path}")
    assert itm.exit_code == itm.EXIT_SUCCESS


@pytest.mark.parametrize("version", VERSION_STRINGS)
def test_redeploy_server(itm, tomcat_manager_server, safe_path, version):
    itm.onecmd_plus_hooks(
        f"deploy server {version} {tomcat_manager_server.warfile} {safe_path}"
    )
    assert itm.exit_code == itm.EXIT_SUCCESS

    itm.onecmd_plus_hooks(
        f"redeploy server {version} {tomcat_manager_server.warfile} {safe_path}"
    )
    assert itm.exit_code == itm.EXIT_SUCCESS

    itm.onecmd_plus_hooks(f"undeploy {version} {safe_path}")
    assert itm.exit_code == itm.EXIT_SUCCESS


@pytest.mark.parametrize("version", VERSION_STRINGS)
def test_deploy_context(itm, tomcat_manager_server, safe_path, version):
    itm.onecmd_plus_hooks(
        f"deploy context {version} {tomcat_manager_server.contextfile} {safe_path}"
    )
    assert itm.exit_code == itm.EXIT_SUCCESS

    itm.onecmd_plus_hooks(f"undeploy {version} {safe_path}")
    assert itm.exit_code == itm.EXIT_SUCCESS


@pytest.mark.parametrize("version", VERSION_STRINGS)
def test_redeploy_context(itm, tomcat_manager_server, safe_path, version):
    itm.onecmd_plus_hooks(
        f"deploy context {version} {tomcat_manager_server.contextfile} {safe_path}"
    )
    assert itm.exit_code == itm.EXIT_SUCCESS

    itm.onecmd_plus_hooks(
        f"redeploy context {version} {tomcat_manager_server.contextfile} {safe_path}"
    )
    assert itm.exit_code == itm.EXIT_SUCCESS

    itm.onecmd_plus_hooks(f"undeploy {version} {safe_path}")
    assert itm.exit_code == itm.EXIT_SUCCESS


@pytest.mark.parametrize("version", VERSION_STRINGS)
def test_deploy_context_warfile(itm, tomcat_manager_server, safe_path, version):
    itm.onecmd_plus_hooks(
        (
            f"deploy context {version} {tomcat_manager_server.contextfile}"
            f" {tomcat_manager_server.warfile} {safe_path}"
        )
    )
    assert itm.exit_code == itm.EXIT_SUCCESS

    itm.onecmd_plus_hooks(f"undeploy {version} {safe_path}")
    assert itm.exit_code == itm.EXIT_SUCCESS


@pytest.mark.parametrize("version", VERSION_STRINGS)
def test_redeploy_context_warfile(itm, tomcat_manager_server, safe_path, version):
    itm.onecmd_plus_hooks(
        (
            f"deploy context {version} {tomcat_manager_server.contextfile}"
            f" {tomcat_manager_server.warfile} {safe_path}"
        )
    )
    assert itm.exit_code == itm.EXIT_SUCCESS

    itm.onecmd_plus_hooks(
        (
            f"redeploy context {version} {tomcat_manager_server.contextfile}"
            f" {tomcat_manager_server.warfile} {safe_path}"
        )
    )
    assert itm.exit_code == itm.EXIT_SUCCESS

    itm.onecmd_plus_hooks(f"undeploy {version} {safe_path}")
    assert itm.exit_code == itm.EXIT_SUCCESS


###
#
# start, stop, restart, reload, sessions, expire
#
###
@pytest.mark.parametrize("version", VERSION_STRINGS)
def test_stop_start(itm, localwar_file, safe_path, version):
    itm.onecmd_plus_hooks(f"deploy local {version} {localwar_file} {safe_path}")
    assert itm.exit_code == itm.EXIT_SUCCESS

    itm.onecmd_plus_hooks(f"stop {version} {safe_path}")
    assert itm.exit_code == itm.EXIT_SUCCESS

    itm.onecmd_plus_hooks(f"start {version} {safe_path}")
    assert itm.exit_code == itm.EXIT_SUCCESS

    itm.onecmd_plus_hooks(f"undeploy {version} {safe_path}")
    assert itm.exit_code == itm.EXIT_SUCCESS


COMMANDS = ["restart", "reload", "sessions"]


@pytest.mark.parametrize("command", COMMANDS)
@pytest.mark.parametrize("version", VERSION_STRINGS)
def test_commands(itm, localwar_file, safe_path, command, version):
    itm.onecmd_plus_hooks(f"deploy local {version} {localwar_file} {safe_path}")
    assert itm.exit_code == itm.EXIT_SUCCESS

    itm.onecmd_plus_hooks(f"{command} {version} {safe_path}")
    assert itm.exit_code == itm.EXIT_SUCCESS

    itm.onecmd_plus_hooks(f"undeploy {version} {safe_path}")
    assert itm.exit_code == itm.EXIT_SUCCESS


@pytest.mark.parametrize("version", VERSION_STRINGS)
def test_expire(itm, localwar_file, safe_path, version):
    itm.onecmd_plus_hooks(f"deploy local {version} {localwar_file} {safe_path}")
    assert itm.exit_code == itm.EXIT_SUCCESS

    itm.onecmd_plus_hooks(f"expire {version} {safe_path} 30")
    assert itm.exit_code == itm.EXIT_SUCCESS

    itm.onecmd_plus_hooks(f"undeploy {version} {safe_path}")
    assert itm.exit_code == itm.EXIT_SUCCESS


###
#
# list
#
###
def parse_apps(lines):
    """helper function to turn colon seperated text into objects"""
    apps = []
    for line in lines.splitlines():
        app = tm.models.TomcatApplication()
        app.parse(line)
        apps.append(app)
    return apps


def test_list_process_apps_empty():
    lines = ""
    itm = tm.InteractiveTomcatManager()
    args = itm.parse_args(itm.list_parser, "")
    apps = parse_apps(lines)
    apps = itm._list_process_apps(apps, args)
    assert isinstance(apps, list)
    assert apps == []


LIST_CMDLINE_BAD = [
    "list -raw",
    "list --raw -b tate",
    "list --by=version",
    "list -s loading",
    "list -sl",
    "list -bs",
]


@pytest.mark.parametrize("cmdline", LIST_CMDLINE_BAD)
def test_list_parse_args_failure(itm, cmdline):
    statement = itm.statement_parser.parse(cmdline)
    with pytest.raises(cmd2.Cmd2ArgparseError):
        itm.parse_args(itm.list_parser, statement.argv)
    assert itm.exit_code == itm.EXIT_USAGE


@pytest.mark.parametrize("raw", ["", "-r", "--raw"])
@pytest.mark.parametrize(
    "state",
    ["", "-s running", "-s stopped", "--state=running", "--state=stopped"],
)
@pytest.mark.parametrize(
    "sort",
    ["", "-b state", "-b path", "--by=state", "--by=path"],
)
def test_list_parse_args(itm_nc, raw, state, sort):
    cmdline = f"list {raw} {state} {sort}"
    statement = itm_nc.statement_parser.parse(cmdline)
    itm_nc.parse_args(itm_nc.list_parser, statement.argv)
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_list_sort_by_state(itm, mocker, capsys):
    raw_apps = """/shiny:stopped:0:shiny##v2.0.6
/:running:0:ROOT
/shiny:running:15:shiny##v2.0.7
/host-manager:running:0:/usr/share/tomcat8-admin/host-manager
/manager:running:0:/usr/share/tomcat8-admin/manager
"""
    expected = """/:running:0:ROOT
/host-manager:running:0:/usr/share/tomcat8-admin/host-manager
/manager:running:0:/usr/share/tomcat8-admin/manager
/shiny:running:15:shiny##v2.0.7
/shiny:stopped:0:shiny##v2.0.6
"""
    # have to mock this here because it messes up prior commands
    # if we do it sooner
    mock_apps = mocker.patch(
        "tomcatmanager.models.TomcatManagerResponse.result",
        create=True,
        new_callable=mock.PropertyMock,
    )
    mock_apps.return_value = raw_apps
    itm.onecmd_plus_hooks("list --raw -b state")
    out, _ = capsys.readouterr()
    assert out == expected


def test_list_sort_by_path(itm, mocker, capsys):
    raw_apps = """/:running:0:ROOT
/shiny:stopped:0:shiny##v2.0.6
/shiny:running:15:shiny##v2.0.7
/host-manager:running:0:/usr/share/tomcat8-admin/host-manager
/manager:running:0:/usr/share/tomcat8-admin/manager
"""
    expected = """/:running:0:ROOT
/host-manager:running:0:/usr/share/tomcat8-admin/host-manager
/manager:running:0:/usr/share/tomcat8-admin/manager
/shiny:stopped:0:shiny##v2.0.6
/shiny:running:15:shiny##v2.0.7
"""
    # have to mock this here because it messes up prior commands
    # if we do it sooner
    mock_apps = mocker.patch(
        "tomcatmanager.models.TomcatManagerResponse.result",
        create=True,
        new_callable=mock.PropertyMock,
    )
    mock_apps.return_value = raw_apps
    itm.onecmd_plus_hooks("list --raw -b path")
    out, _ = capsys.readouterr()
    assert out == expected


def test_list_state_running(itm, mocker, capsys):
    raw_apps = """/:running:0:ROOT
/shiny:stopped:17:shiny##v2.0.6
/shiny:running:15:shiny##v2.0.7
/host-manager:stopped:0:/usr/share/tomcat8-admin/host-manager
/manager:running:0:/usr/share/tomcat8-admin/manager
"""
    expected = """/:running:0:ROOT
/manager:running:0:/usr/share/tomcat8-admin/manager
/shiny:running:15:shiny##v2.0.7
"""
    # have to mock this here because it messes up prior commands
    # if we do it sooner
    mock_apps = mocker.patch(
        "tomcatmanager.models.TomcatManagerResponse.result",
        create=True,
        new_callable=mock.PropertyMock,
    )
    mock_apps.return_value = raw_apps
    itm.onecmd_plus_hooks("list --raw -s running")
    out, _ = capsys.readouterr()
    assert out == expected


USAGE_ERRORS = [
    "start",
    "stop",
    "restart",
    "reload",
    "sessions",
    "expire",
    "expire /path",
    "deploy local",
    "redeploy local",
    "deploy local /tmp/warfile.war",
    "redeploy local /tmp/warfile.war",
    "deploy server",
    "redeploy server",
    "deploy server /tmp/warfile.war",
    "redeploy server /tmp/warfile.war",
    "deploy context /tmp/context.xml",
    "redeploy context /tmp/context.xml",
]


@pytest.mark.parametrize("cmdline", USAGE_ERRORS)
def test_usage_errors(itm, cmdline, capsys):
    # suppress feedback because we are checking for usage
    itm.quiet = True
    itm.onecmd_plus_hooks(cmdline)
    out, err = capsys.readouterr()
    assert not out
    assert err.strip().startswith("usage: ")
    assert itm.exit_code == itm.EXIT_USAGE
