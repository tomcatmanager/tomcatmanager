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

import importlib.resources as importlib_resources

try:
    _ = importlib_resources.files
except AttributeError:  # pragma: nocover
    # python < 3.8 doesn't have .files in the standard library importlib.resources
    # we'll go get the one from pypi, which has it
    # pylint: disable=import-error
    import importlib_resources  # type: ignore

import pathlib
import textwrap
from unittest import mock
import uuid

import pytest
import tomlkit

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
# test usage and help
#
###

#
# all of these comands should generate a usage message
USAGE_COMMANDS = [
    "config",
    "connect",
    "deploy",
    "deploy unknown",
    "deploy local",
    "deploy server",
    "deploy context",
    "deploy local /tmp/warfile.war",
    "deploy server /tmp/warfile.war",
    "deploy context /tmp/contextfile.xml",
    "redeploy",
    "redeploy unknown",
    "redeploy unknown unknown",
    "redeploy local",
    "redeploy server",
    "redeploy context",
    "redeploy local /tmp/warfile.war",
    "redeploy server /tmp/warfile.war",
    "redeploy context /tmp/contextfile.xml",
    "start",
    "stop",
    "reload",
    "restart",
    "sessions",
    "theme",
    "theme invalid",
    "expire",
    "expire /tmp/somepath",
]


@pytest.mark.parametrize("command", USAGE_COMMANDS)
def test_command_usage(itm, command):
    # we need to be connected for these to generate the proper messages
    itm.exit_code = itm.EXIT_ERROR
    itm.onecmd_plus_hooks(command)
    assert itm.exit_code == itm.EXIT_USAGE


HELP_COMMANDS = [
    "config",
    "settings",
    "theme",
    "connect",
    "which",
    "disconnect",
    "deploy",
    "redeploy",
    "undeploy",
    "start",
    "stop",
    "reload",
    "restart",
    "sessions",
    "expire",
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
    "version",
    "license",
]


# exit_code omitted because it doesn't respond
# to -h or --help
@pytest.mark.parametrize("command", HELP_COMMANDS)
def test_command_help(itm_nc, command):
    # help should work without us being connected to a server
    itm_nc.exit_code = itm_nc.EXIT_ERROR
    itm_nc.onecmd_plus_hooks(f"{command} -h")
    assert itm_nc.exit_code == itm_nc.EXIT_USAGE

    itm_nc.exit_code = itm_nc.EXIT_ERROR
    itm_nc.onecmd_plus_hooks(f"{command} --help")
    assert itm_nc.exit_code == itm_nc.EXIT_USAGE


# copy the list
HELP_ARGPARSERS = list(HELP_COMMANDS)
# there is an argparser for exit_code, but it's only used
# to generate the help
HELP_ARGPARSERS.append("exit_code")
# remove subcommand argparsers from this list, they will be
# tested separately below
HELP_ARGPARSERS.remove("deploy")
HELP_ARGPARSERS.remove("redeploy")
HELP_ARGPARSERS.remove("theme")


@pytest.mark.parametrize("command", HELP_ARGPARSERS)
def test_help_matches_argparser(itm_nc, command, capsys):
    cmdline = f"help {command}"
    itm_nc.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    parser_func = getattr(itm_nc, f"{command}_parser")
    assert out.strip() == parser_func.format_help().strip()
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_help_set(itm_nc, capsys):
    # set gets it's own testing mechanism because it doesn't use argparser
    # it needs to preserve quotes and such so toml parsing works as expected
    cmdline = "help set"
    itm_nc.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "change a program setting" in out
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


DEPLOY_USAGE_COMMANDS = [
    "help deploy",
    "help deploy invalid",
    "help deploy invalid invalid",
    "help redeploy",
    "help redeploy invalid",
    "help redeploy invalid invalid",
]


@pytest.mark.parametrize("command", DEPLOY_USAGE_COMMANDS)
def test_help_deploy(itm_nc, command, capsys):
    itm_nc.onecmd_plus_hooks(command)
    out, _ = capsys.readouterr()
    assert "deployment_method" in out
    assert "local" in out
    assert "server" in out
    assert "context" in out
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_help_deploy_local(itm_nc, capsys):
    cmdline = "help deploy local"
    itm_nc.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "local file system" in out
    assert "warfile" in out
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_help_deploy_server(itm_nc, capsys):
    cmdline = "help deploy server"
    itm_nc.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "server file system" in out
    assert "warfile" in out
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_help_deploy_context(itm_nc, capsys):
    cmdline = "help deploy context"
    itm_nc.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "server file system" in out
    assert "warfile" in out
    assert "contextfile" in out
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


THEME_USAGE_COMMANDS = [
    "help theme",
    "help theme invalid",
    "help theme invalid invalid",
]


@pytest.mark.parametrize("command", THEME_USAGE_COMMANDS)
def test_help_theme(itm_nc, command, capsys):
    itm_nc.onecmd_plus_hooks(command)
    out, _ = capsys.readouterr()
    assert "action" in out
    assert "list" in out
    assert "create" in out
    assert "dir" in out
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_help_theme_list(itm_nc, capsys):
    cmdline = "help theme list"
    itm_nc.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "list all themes" in out
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_help_theme_clone(itm_nc, capsys):
    cmdline = "help theme clone"
    itm_nc.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "clone a theme" in out
    assert "name" in out
    assert "new_name" in out
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_help_theme_edit(itm_nc, capsys):
    cmdline = "help theme edit"
    itm_nc.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "edit a user theme" in out
    assert "name" in out
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_help_theme_create(itm_nc, capsys):
    cmdline = "help theme create"
    itm_nc.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "create a new user theme" in out
    assert "name" in out
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_help_theme_delete(itm_nc, capsys):
    cmdline = "help theme delete"
    itm_nc.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "delete a user theme" in out
    assert "name" in out
    assert "--force" in out
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_help_theme_dir(itm_nc, capsys):
    cmdline = "help theme dir"
    itm_nc.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "theme directory" in out
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_help(itm_nc, capsys):
    cmdline = "help"
    itm_nc.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "Connecting to a Tomcat server" in out
    assert "Managing applications" in out
    assert "Server information" in out
    assert "Settings, configuration, and tools" in out
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_help_invalid(itm_nc, capsys):
    cmdline = "help invalidcommand"
    itm_nc.onecmd_plus_hooks(cmdline)
    _, err = capsys.readouterr()
    assert err
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR


###
#
# test config and settings
#
###
BOOLEANS = [
    ("1", True),
    ("0", False),
    ("y", True),
    ("Y", True),
    ("yes", True),
    ("Yes", True),
    ("YES", True),
    ("n", False),
    ("N", False),
    ("no", False),
    ("No", False),
    ("NO", False),
    ("on", True),
    ("On", True),
    ("ON", True),
    ("off", False),
    ("Off", False),
    ("OFF", False),
    ("t", True),
    ("true", True),
    ("True", True),
    ("TRUE", True),
    ("f", False),
    ("false", False),
    ("False", False),
    ("FALSE", False),
    (True, True),
    (False, False),
]


@pytest.mark.parametrize("param, value", BOOLEANS)
def test_convert_to_boolean_valid(itm_nc, param, value):
    assert itm_nc.convert_to_boolean(param) == value


NOT_BOOLEANS = [
    None,
    "",
    10,
    "ace",
]


@pytest.mark.parametrize("param", NOT_BOOLEANS)
def test_convert_to_boolean_invalid(itm_nc, param):
    with pytest.raises(ValueError):
        itm_nc.convert_to_boolean(param)


LITERALS = [
    ("fred", "fred"),
    ("fred ", "'fred '"),
    ("can't ", '"can\'t "'),
    ('b"d', "'b\"d'"),
    ("b'|\"d", "'b\\'|\"d'"),
]


@pytest.mark.parametrize("param, value", LITERALS)
def test_pythonize(param, value):
    itm = tm.InteractiveTomcatManager()
    assert itm._pythonize(param) == value


def test_appdirs():
    itm = tm.InteractiveTomcatManager()
    assert itm.appdirs


def test_config_file_property():
    itm = tm.InteractiveTomcatManager()
    # don't care where it is, just care that there is one
    assert itm.config_file
    # if appdirs doesn't exist, config_file shouldn't either
    itm.appdirs = None
    assert not itm.config_file


def test_config_file_old_property():
    itm = tm.InteractiveTomcatManager()
    # don't care where it is, just care that there is one
    assert itm.config_file_old
    # if appdirs doesn't exist, config_file shouldn't either
    itm.appdirs = None
    assert not itm.config_file_old


def test_history_file_property():
    itm = tm.InteractiveTomcatManager()
    # don't care where it is, just care that there is one
    assert itm.history_file
    # if appdirs doesn't exist, config_file shouldn't either
    itm.appdirs = None
    assert not itm.history_file


def test_config_edit(itm_nc, mocker):
    itm_nc.editor = "fooedit"
    mock_os_system = mocker.patch("os.system")
    itm_nc.onecmd_plus_hooks("config edit")
    assert mock_os_system.call_count == 1
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_config_edit_no_editor(itm_nc, capsys):
    itm_nc.editor = None
    itm_nc.onecmd_plus_hooks("config edit")
    out, err = capsys.readouterr()
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR
    assert not out
    assert err.startswith("no editor: ")


def test_config_edit_sets_defaults(itm_nc, tmp_path, mocker):
    fname = pathlib.Path(tmp_path / "someconfig.toml")
    config_file = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.config_file",
        new_callable=mock.PropertyMock,
    )
    config_file.return_value = fname
    itm_nc.prompt = "typehere> "
    # we need an editor set
    itm_nc.editor = "fooedit"
    # but we prevent the editor from executing
    mock_os_system = mocker.patch("os.system")

    itm_nc.onecmd_plus_hooks("config edit")
    assert mock_os_system.call_count == 1
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS
    assert itm_nc.prompt == "tomcat-manager> "


def test_config_edit_no_configfile(itm_nc, mocker, capsys):
    config_file = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.config_file",
        new_callable=mock.PropertyMock,
    )
    config_file.return_value = None
    # we need an editor set
    itm_nc.editor = "fooedit"
    # but we prevent the editor from executing
    mock_os_system = mocker.patch("os.system")

    itm_nc.onecmd_plus_hooks("config edit")
    _, err = capsys.readouterr()
    assert mock_os_system.call_count == 0
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR
    assert "could not figure out where configuration" in err


def test_config_invalid_action(itm_nc, capsys):
    itm_nc.onecmd_plus_hooks("config bogus")
    out, err = capsys.readouterr()
    assert itm_nc.exit_code == itm_nc.EXIT_USAGE
    assert not out
    assert err.startswith("usage: ")


def test_config_file_command(itm_nc, mocker, capsys):
    fname = pathlib.Path("/tmp/someconfig.toml")
    config_file = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.config_file",
        new_callable=mock.PropertyMock,
    )
    config_file.return_value = fname

    itm_nc.onecmd_plus_hooks("config file")
    out, _ = capsys.readouterr()
    assert out == f"{str(fname)}\n"
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_config_convert_no_config(itm_nc, tmp_path, mocker, capsys):
    # verify conversion behavior when neither ini nor toml config files exist
    inifile = tmp_path / "tomcat-manager.ini"
    tomlfile = tmp_path / "tomcat-manager.toml"

    config_file = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.config_file",
        new_callable=mock.PropertyMock,
    )
    config_file.return_value = tomlfile

    config_file = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.config_file_old",
        new_callable=mock.PropertyMock,
    )
    config_file.return_value = inifile

    itm_nc.onecmd_plus_hooks("config convert")
    _, err = capsys.readouterr()

    assert "old configuration file does not exist: nothing to convert" in err
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR


def test_config_convert(itm_nc, tmp_path, mocker, capsys):
    iniconfig = """#
[settings]
prompt='tm> '
debug=True
echo=False
timing=false
timeout=20.0
editor=/usr/local/bin/zile

[server1]
url=https://www.example1.com
user=someuser
password=somepassword

[server2]
url = https://www.example2.com/some/path/to/tomcat
cert = ~/certs/my.cert
key = ~/keys/mykey
verify = False
"""
    tomlconfig = """[settings]
prompt = "tm> "
debug = true
echo = false
timing = false
timeout = 20.0
editor = "/usr/local/bin/zile"

[server1]
url = "https://www.example1.com"
user = "someuser"
password = "somepassword"

[server2]
url = "https://www.example2.com/some/path/to/tomcat"
cert = "~/certs/my.cert"
key = "~/keys/mykey"
verify = false
"""
    inifile = tmp_path / "tomcat-manager.ini"
    tomlfile = tmp_path / "tomcat-manager.toml"

    config_file = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.config_file",
        new_callable=mock.PropertyMock,
    )
    config_file.return_value = tomlfile

    config_file = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.config_file_old",
        new_callable=mock.PropertyMock,
    )
    config_file.return_value = inifile

    with open(inifile, "w", encoding="utf-8") as iniobj:
        iniobj.write(iniconfig)

    itm_nc.onecmd_plus_hooks("config convert")
    _, err = capsys.readouterr()

    assert "converting old configuration file to new format" in err
    assert "reloading configuration" in err
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS

    with open(tomlfile, "r", encoding="utf-8") as tomlobj:
        test_tomlconfig = tomlobj.read()
        assert test_tomlconfig == tomlconfig


def test_config_convert_invalid_setting(itm_nc, tmp_path, mocker, capsys):
    iniconfig = """#
[settings]
prompt='tm> '
debug=True
timeout=20.0
editor=/usr/local/bin/zile
invalidsetting=this should break

[server1]
url=https://www.example1.com
user=someuser
password=somepassword

[server2]
url = https://www.example2.com/some/path/to/tomcat
cert = ~/certs/my.cert
key = ~/keys/mykey
verify = False
"""
    inifile = tmp_path / "tomcat-manager.ini"
    tomlfile = tmp_path / "tomcat-manager.toml"

    config_file = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.config_file",
        new_callable=mock.PropertyMock,
    )
    config_file.return_value = tomlfile

    config_file = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.config_file_old",
        new_callable=mock.PropertyMock,
    )
    config_file.return_value = inifile

    with open(inifile, "w", encoding="utf-8") as iniobj:
        iniobj.write(iniconfig)

    itm_nc.onecmd_plus_hooks("config convert")
    _, err = capsys.readouterr()

    assert "converting old configuration file to new format" in err
    assert "conversion failed" in err
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR


def test_config_convert_both_exist(itm_nc, tmp_path, mocker, capsys):
    inifile = tmp_path / "tomcat-manager.ini"
    inifile.touch()
    tomlfile = tmp_path / "tomcat-manager.toml"
    tomlfile.touch()

    config_file = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.config_file",
        new_callable=mock.PropertyMock,
    )
    config_file.return_value = tomlfile

    config_file = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.config_file_old",
        new_callable=mock.PropertyMock,
    )
    config_file.return_value = inifile

    itm_nc.onecmd_plus_hooks("config convert")
    _, err = capsys.readouterr()

    assert "configuration file exists: cowardly refusing to overwrite it" in err
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR


def test_load_config(itm_with_config):
    prompt = str(uuid.uuid1())
    config_string = f"""
        [settings]
        prompt = "{prompt}"
        """
    itm = itm_with_config(config_string)
    assert itm.prompt == prompt


def test_load_config_file_not_found():
    with mock.patch("builtins.open", mock.mock_open()) as mocked_open:
        mocked_open.side_effect = FileNotFoundError()
        itm = tm.InteractiveTomcatManager()
        assert len(itm.config.keys()) == 0


def test_noload_config(capsys):
    # check the status message for skipping the load of the config file
    itm = tm.InteractiveTomcatManager(loadconfig=False)
    # we need some command to run, it doesn't matter what it is
    itm.onecmd_plus_hooks("version")
    _, err = capsys.readouterr()
    assert "skipping load of configuration file" in err


def test_load_config_bogus_setting(itm_with_config):
    config_string = """
        [settings]
        bogus = true
        """
    # this shouldn't throw any exceptions
    _ = itm_with_config(config_string)


def test_load_config_not_boolean(itm_nc, itm_with_config):
    config_string = """
        [settings]
        echo = "not a boolean"
        """
    # this shouldn't throw any exceptions
    itm = itm_with_config(config_string)
    # make sure echo didn't change
    assert itm.echo == itm_nc.echo


def test_load_config_echo_false(itm_with_config):
    config_string = """
        [settings]
        echo = false
        """
    # this shouldn't throw any exceptions
    itm = itm_with_config(config_string)
    assert itm.echo is False


def test_load_config_echo_true(itm_with_config):
    config_string = """
        [settings]
        echo = true
        """
    # this shouldn't throw any exceptions
    itm = itm_with_config(config_string)
    # make sure the echo setting is the same
    # as when we don't load a config file
    assert itm.echo is True


def test_load_config_not_integer(itm_nc, itm_with_config):
    config_string = """
        [settings]
        timeout = "notaninteger"
        """
    # this shouldn't throw any exceptions
    itm = itm_with_config(config_string)
    # make sure the timeout setting is the same
    # as when we don't load a config file
    assert itm.timeout == itm_nc.timeout


def test_load_config_syntax_error(itm_nc, itm_with_config, capsys):
    config_string = """
        [settings]
        prompt = "tm>
        """
    itm = itm_with_config(config_string)
    _, err = capsys.readouterr()
    assert "error loading configuration file" in err
    # make sure that loading the broken configuration file didn't
    # change the prompt
    assert itm.prompt == itm_nc.prompt


def test_show_invalid(itm_nc, capsys):
    # make sure that the show command, which we have overridden, doesn't
    # do the thing that it does by default in cmd2.Cmd
    itm_nc.onecmd_plus_hooks("show")
    out, err = capsys.readouterr()
    assert itm_nc.exit_code == itm_nc.EXIT_COMMAND_NOT_FOUND
    assert not out
    assert "unknown command: show" in err


def test_settings_noargs(itm_nc, capsys):
    itm_nc.onecmd_plus_hooks("settings")
    out, _ = capsys.readouterr()
    # make sure there is a line for each setting
    assert len(out.splitlines()) == len(itm_nc.settables)
    # check the first setting is "debug", they are sorted in
    # alphabetical order, so this one should come out first
    assert out.splitlines()[0].split("=")[0].strip() == "debug"
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_settings_valid_setting(itm_nc, capsys):
    itm_nc.onecmd_plus_hooks("settings prompt")
    out, _ = capsys.readouterr()
    assert out.startswith(f'prompt = "{itm_nc.prompt}" ')
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_settings_invalid_setting(itm_nc, capsys):
    itm_nc.onecmd_plus_hooks("settings bogus")
    out, err = capsys.readouterr()
    assert not out
    assert err == "unknown setting: 'bogus'\n"
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR


def test_set_noargs(itm_nc, capsys):
    itm_nc.onecmd_plus_hooks("set")
    out, _ = capsys.readouterr()
    # make sure there is a line for each setting
    assert len(out.splitlines()) == len(itm_nc.settables)
    # check the first setting is "debug", they are sorted in
    # alphabetical order, so this one should come out first
    assert out.splitlines()[0].split("=")[0].strip() == "debug"
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_set_help(itm_nc, capsys):
    itm_nc.onecmd_plus_hooks("set -h")
    out, _ = capsys.readouterr()
    assert "change a program setting" in out
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_set_string(itm_nc):
    prompt = str(uuid.uuid1())
    itm_nc.onecmd_plus_hooks(f"set prompt = '{prompt}'")
    assert itm_nc.prompt == prompt
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_set_mismatched_quotes(itm_nc, capsys):
    itm_nc.onecmd_plus_hooks("set prompt = notquoted")
    _, err = capsys.readouterr()
    assert "invalid syntax" in err
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR


def test_set_quiet_to_string_nodebug(itm_nc, capsys):
    itm_nc.debug = False
    itm_nc.onecmd_plus_hooks('set debug = "shouldbeboolean"')
    _, err = capsys.readouterr()
    # it would be nice if we could check what the error message is, but
    # it's generated by CMD, so we don't get to control when it changes
    assert err
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR


def test_set_quiet_to_string_debug(itm_nc, capsys):
    itm_nc.debug = True
    itm_nc.onecmd_plus_hooks('set debug = "shouldbeboolean"')
    _, err = capsys.readouterr()
    # it would be nice if we could check what the error message is, but
    # it's generated by CMD, so we don't get to control when it changes
    assert err
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR


def test_set_float_valid(itm_nc):
    itm_nc.timeout = 10.0
    itm_nc.onecmd_plus_hooks("set timeout = 5.5")
    assert itm_nc.timeout == 5.5
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_set_float_invalid(itm_nc):
    itm_nc.timeout = 10.0
    itm_nc.onecmd_plus_hooks("set timeout = joe")
    assert itm_nc.timeout == 10.0
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR


def test_set_float_invalid_debug(itm_nc):
    itm_nc.timeout = 10.0
    itm_nc.onecmd_plus_hooks("set timeout = joe")
    assert itm_nc.timeout == 10.0
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR


def test_set_boolean_true(itm_nc):
    itm_nc.echo = False
    itm_nc.onecmd_plus_hooks("set echo = true")
    assert itm_nc.echo is True
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_set_boolean_false(itm_nc):
    itm_nc.echo = True
    itm_nc.onecmd_plus_hooks("set echo = false")
    assert itm_nc.echo is False
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_set_boolean_invalid(itm_nc):
    itm_nc.echo = False
    itm_nc.onecmd_plus_hooks("set echo = notaboolean")
    assert itm_nc.echo is False
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR


def test_set_boolean_zero(itm_nc):
    itm_nc.echo = True
    itm_nc.onecmd_plus_hooks("set echo = 0")
    assert itm_nc.echo is False
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_set_debug_invalid(itm_nc):
    itm_nc.echo = False
    itm_nc.onecmd_plus_hooks("set echo = notaboolean")
    assert itm_nc.echo is False
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR


def test_set_unknown_setting(itm_nc, capsys):
    itm_nc.onecmd_plus_hooks("set fred = 'somevalue'")
    _, err = capsys.readouterr()
    assert "unknown setting" in err
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR


def test_set_with_invalid_param(itm_nc):
    # this uuid won't be in itm.settables
    invalid_setting = str(uuid.uuid1())
    with pytest.raises(ValueError):
        # pylint: disable=protected-access
        itm_nc._change_setting(invalid_setting, "someval")


def test_timeout_property(itm_nc):
    timeout = 8.5
    # set this to a value that we know will cause it to change when we execute
    # the command
    itm_nc.timeout = 5
    assert itm_nc.tomcat.timeout == 5
    itm_nc.onecmd_plus_hooks(f"set timeout = {timeout}")
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS
    assert itm_nc.timeout == timeout
    assert itm_nc.tomcat.timeout == timeout


SETTINGS_SUCCESSFUL = [
    ("set prompt = 'tm>'", "tm>"),
    ("set prompt = 'tm> '", "tm> "),
    ('set prompt = "t m>"', "t m>"),
    ('set prompt = "tm> "', "tm> "),
    ('set prompt = "tm> "   # some comment here', "tm> "),
    ('set prompt = "t\'m> "', "t'm> "),
    # single quote embedded in triple quotes
    ('set prompt = """h' + "'" + 'i"""', "h'i"),
]


@pytest.mark.parametrize("arg, value", SETTINGS_SUCCESSFUL)
def test_do_set_success(itm_nc, arg, value):
    itm_nc.onecmd_plus_hooks(arg)
    assert itm_nc.prompt == value
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


SETTINGS_FAILURE = [
    "set thisisntaparam=somevalue",
    "set thisisntaparam",
]


@pytest.mark.parametrize("arg", SETTINGS_FAILURE)
def test_do_set_fail(itm_nc, arg):
    itm_nc.onecmd_plus_hooks(arg)
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR


PREFIXES = [
    ("--", "--"),
    ("*", "*"),
    (">>>", ">>>"),
    # with no prefix, we should see the connected message
    ("", "connect"),
]


@pytest.mark.parametrize("prefix, expected", PREFIXES)
def test_status_prefix(tomcat_manager_server, itm_nc, prefix, expected, capsys):
    # since we are testing the output of the connect command
    # use itm_nc instead of itm fixture
    itm_nc.status_prefix = prefix
    itm_nc.quiet = False
    itm_nc.onecmd_plus_hooks(tomcat_manager_server.connect_command)
    _, err = capsys.readouterr()
    assert err.startswith(expected)
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_status_animation(itm_nc):
    itm_nc.onecmd_plus_hooks("set status_animation = 'dots'")
    assert itm_nc.status_animation == "dots"
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS
    # do another one just incase the default ever got set to dots
    itm_nc.onecmd_plus_hooks("set status_animation = 'line'")
    assert itm_nc.status_animation == "line"
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_status_animation_invalid(itm_nc, capsys):
    itm_nc.onecmd_plus_hooks("set status_animation = 'invalid'")
    _, err = capsys.readouterr()
    assert "invalid" in err
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR


def test_status_animation_none(itm_nc):
    itm_nc.onecmd_plus_hooks("set status_animation = ''")
    assert itm_nc.status_animation == ""
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


###
#
# test theme setting, loading, and commands
#
###
def test_theme_default_none(itm_nc):
    assert itm_nc.theme == ""


def test_theme_use_embedded(itm_nc, tmp_path, mocker):
    theme = "default-dark"
    # patch the empty temporary directory into user_theme_dir
    # to make sure we are loading the built-in theme
    mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
        new_callable=mock.PropertyMock,
        return_value=tmp_path,
    )
    assert not itm_nc.theme
    itm_nc.onecmd_plus_hooks(f"set theme = '{theme}'")
    assert itm_nc.theme == theme


def test_theme_invalid(itm_nc, capsys):
    theme = str(uuid.uuid1())
    assert not itm_nc.theme
    itm_nc.onecmd_plus_hooks(f"set theme = '{theme}'")
    out, err = capsys.readouterr()
    assert not itm_nc.theme
    assert err
    assert not out


def test_resolve_theme_builtin(itm_nc, tmp_path, mocker):
    theme_name = "default-dark"
    # patch the empty temporary directory into user_theme_dir
    # this avoids the test failing if the user running the test
    # happens to have cloned one of the built-in themes
    mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
        new_callable=mock.PropertyMock,
        return_value=tmp_path,
    )
    location, path = itm_nc._resolve_theme(theme_name)
    assert location == tm.interactive_tomcat_manager.ThemeLocation.BUILTIN
    assert path
    assert str(importlib_resources.files("tomcatmanager.themes")) in str(path)
    assert theme_name in str(path)


def test_resolve_theme_invalid_name(itm_nc):
    # shouldn't find this random uuid as a theme
    theme = str(uuid.uuid1())
    location, path = itm_nc._resolve_theme(theme)
    assert not location
    assert not path


def test_resolve_theme_user(itm_nc, tmp_path, mocker, capsys):
    theme = str(uuid.uuid1())
    # get a temporary directory
    themefile = tmp_path / f"{theme}.toml"
    with open(themefile, "w", encoding="utf-8") as file_var:
        file_var.write("tm.error = 'red'\n")
    # patch the temporary directory into user_theme_dir
    mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
        new_callable=mock.PropertyMock,
        return_value=tmp_path,
    )
    # now that we are all set up, go try and load the theme
    itm_nc.onecmd_plus_hooks(f"set theme = '{theme}'")
    out, _ = capsys.readouterr()
    assert not out
    assert itm_nc.theme == theme


def test_apply_theme_file_parse_error(itm_nc, tmp_path, mocker, capsys):
    theme = "someusertheme"
    # get a temporary directory
    themefile = tmp_path / f"{theme}.toml"
    with open(themefile, "w", encoding="utf-8") as file_var:
        file_var.write("tm.error = 'red\n")
    # patch the temporary directory into user_theme_dir
    mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
        new_callable=mock.PropertyMock,
        return_value=tmp_path,
    )
    # now that we are all set up, go try and load the theme
    itm_nc.onecmd_plus_hooks(f"set theme = '{theme}'")
    out, err = capsys.readouterr()
    assert err
    assert not out
    assert not itm_nc.theme
    assert itm_nc.theme == ""


def test_apply_theme_permission_error(itm_nc, tmp_path, mocker, capsys):
    theme = "someusertheme"
    # get a temporary directory
    themefile = tmp_path / f"{theme}.toml"
    with open(themefile, "w", encoding="utf-8") as file_var:
        file_var.write("tm.error = 'red'\n")
    # patch the temporary directory into user_theme_dir
    mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
        new_callable=mock.PropertyMock,
        return_value=tmp_path,
    )
    # patch open to throw a permission error
    with mock.patch("builtins.open", mock.mock_open()) as mocked_open:
        mocked_open.side_effect = PermissionError()
        # now that we are all set up, go try and load the theme
        itm_nc.onecmd_plus_hooks(f"set theme = '{theme}'")
        out, err = capsys.readouterr()
        assert err
        assert not out
        assert not itm_nc.theme


def test_apply_theme_invalid_theme_color(itm_nc, tmp_path, mocker, capsys):
    theme = "someusertheme"
    # get a temporary directory
    themefile = tmp_path / f"{theme}.toml"
    with open(themefile, "w", encoding="utf-8") as file_var:
        file_var.write("tm.error = 'dodget_blue2'\n")
    # patch the temporary directory into user_theme_dir
    mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
        new_callable=mock.PropertyMock,
        return_value=tmp_path,
    )
    # now that we are all set up, go try and load the theme
    itm_nc.onecmd_plus_hooks(f"set theme = '{theme}'")
    out, err = capsys.readouterr()
    assert err
    assert not out
    assert not itm_nc.theme
    assert itm_nc.theme == ""


def test_user_theme_dir(itm_nc):
    # there should be a theme dir...
    assert "themes" in str(itm_nc.user_theme_dir)
    # unless appdirs doesn't exist
    itm_nc.appdirs = None
    assert not itm_nc.user_theme_dir


def test_theme_dir(itm_nc, capsys):
    itm_nc.onecmd_plus_hooks("theme dir")
    out, err = capsys.readouterr()
    assert out.rstrip() == str(itm_nc.user_theme_dir)
    assert not err


def test_theme_list(itm_nc, capsys):
    # turn off the status output
    itm_nc.quiet = True
    itm_nc.onecmd_plus_hooks("theme list")
    out, err = capsys.readouterr()
    assert not err


def test_theme_list_open_err(itm_nc, tmp_path, mocker):
    # point the user theme dir to our temporary directory
    # to make sure there are no user themes
    mock_theme_dir = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
        new_callable=mock.PropertyMock,
    )
    mock_theme_dir.return_value = tmp_path
    user_theme_file = tmp_path / "usertheme.toml"
    # write an empty user theme file
    with open(user_theme_file, "w", encoding="utf-8"):
        pass

    # generate errors when opening files
    mock_open = mocker.patch("pathlib.Path.open")
    mock_open.side_effect = FileNotFoundError()
    itm_nc.onecmd_plus_hooks("theme list")
    # we have two built-in themes and one user theme
    # so the mock should have been called three times
    # and thrown three OSErrors
    assert mock_open.call_count == 3


def test_theme_list_toml_err(itm_nc, tmp_path, mocker, capsys):
    # put one user theme in, but it doesn't matter what's in there
    # because we are going to mock things so toml parsing throws
    # an error
    mock_theme_dir = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
        new_callable=mock.PropertyMock,
    )
    mock_theme_dir.return_value = tmp_path
    user_theme_file = tmp_path / "usertheme.toml"
    # write an empty user theme file
    with open(user_theme_file, "w", encoding="utf-8"):
        pass

    # generate errors when loading theme files
    mock_load = mocker.patch("tomlkit.load")
    mock_load.side_effect = tomlkit.exceptions.TOMLKitError()
    # suppress feedback
    itm_nc.quiet = True
    itm_nc.onecmd_plus_hooks("theme list")
    # we have two built-in themes, and one user theme,
    # so the mock should have been called 3 times
    assert mock_load.call_count == 3
    out, err = capsys.readouterr()
    assert not err
    # even with the errors, we should get output, but we aren't going
    # to try and parse it
    assert out


def test_theme_edit_current_theme(itm_nc, tmp_path, mocker, response_with):
    # set an editor so we are sure cmd2 will try and call the editor
    itm_nc.editor = "fooedit"
    # point the user theme dir to our temporary directory
    theme_dir_mock = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
        new_callable=mock.PropertyMock,
    )
    theme_dir_mock.return_value = tmp_path
    # prevent the system call
    mock_os_system = mocker.patch("os.system")
    # mock the network request to the gallery
    response = response_with(404, "")
    mocker.patch("requests.get", return_value=response)

    itm_nc.onecmd_plus_hooks("theme clone default-dark")
    itm_nc.onecmd_plus_hooks("set theme='default-dark'")
    itm_nc.onecmd_plus_hooks("theme edit")
    # but let's check to make sure the editor was called
    assert mock_os_system.call_count == 1
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_theme_edit_named_theme(itm_nc, tmp_path, mocker, response_with):
    # set an editor so we are sure cmd2 will try and call the editor
    itm_nc.editor = "fooedit"
    # point the user theme dir to our temporary directory
    theme_dir_mock = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
        new_callable=mock.PropertyMock,
    )
    theme_dir_mock.return_value = tmp_path
    # prevent the system call
    mock_os_system = mocker.patch("os.system")
    # mock the network request to the gallery
    response = response_with(404, "")
    mocker.patch("requests.get", return_value=response)

    itm_nc.onecmd_plus_hooks("theme clone default-light")
    itm_nc.onecmd_plus_hooks("theme edit default-light")
    # but let's check to make sure the editor was called
    assert mock_os_system.call_count == 1
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_theme_edit_builtin(itm_nc, tmp_path, mocker, capsys):
    # set an editor so we are sure cmd2 will try and call the editor
    itm_nc.editor = "fooedit"
    # point the user theme dir to our temporary directory
    theme_dir_mock = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
        new_callable=mock.PropertyMock,
    )
    theme_dir_mock.return_value = tmp_path
    # prevent the system call
    mock_os_system = mocker.patch("os.system")
    itm_nc.onecmd_plus_hooks("theme edit default-light")
    # but let's check to make sure the editor was not called
    assert mock_os_system.call_count == 0
    out, err = capsys.readouterr()
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR
    assert "theme is not editable" in err
    assert not out


def test_theme_edit_unknown_theme(itm_nc, tmp_path, mocker, capsys):
    # set an editor so we are sure cmd2 will try and call the editor
    itm_nc.editor = "fooedit"
    # point the user theme dir to our temporary directory
    theme_dir_mock = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
        new_callable=mock.PropertyMock,
    )
    theme_dir_mock.return_value = tmp_path
    # prevent the system call
    mock_os_system = mocker.patch("os.system")
    itm_nc.onecmd_plus_hooks("theme edit bogus")
    # but let's check to make sure the editor was not called
    assert mock_os_system.call_count == 0
    out, err = capsys.readouterr()
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR
    assert "unknown theme" in err
    assert not out


def test_theme_edit_no_theme(itm_nc, tmp_path, mocker, capsys):
    # set an editor so we are sure cmd2 will try and call the editor
    itm_nc.editor = "fooedit"
    # point the user theme dir to our temporary directory
    theme_dir_mock = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
        new_callable=mock.PropertyMock,
    )
    theme_dir_mock.return_value = tmp_path
    # prevent the system call
    mock_os_system = mocker.patch("os.system")
    itm_nc.onecmd_plus_hooks("theme edit")
    # but let's check to make sure the editor was not called
    assert mock_os_system.call_count == 0
    out, err = capsys.readouterr()
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR
    assert "syntax error: no theme given" in err
    assert not out


def test_theme_edit_no_editor(itm_nc, capsys):
    # make sure we have no editor, which will trigger the desired error
    itm_nc.editor = ""
    itm_nc.onecmd_plus_hooks("theme edit")
    out, err = capsys.readouterr()
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR
    assert "no editor:" in err
    assert not out


def test_theme_edit_error_applying(itm_nc, tmp_path, mocker, response_with):
    # if we edit the current theme, we have to reapply it after the editor
    # closes. Simulate an error in applying the theme (i.e. like one that would)
    # be generated if you had a toml syntax error
    # set an editor so we are sure cmd2 will try and call the editor
    itm_nc.editor = "fooedit"
    # point the user theme dir to our temporary directory
    theme_dir_mock = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
        new_callable=mock.PropertyMock,
    )
    theme_dir_mock.return_value = tmp_path
    # mock the network request to the gallery
    response = response_with(404, "")
    mocker.patch("requests.get", return_value=response)

    itm_nc.onecmd_plus_hooks("theme clone default-dark")
    itm_nc.onecmd_plus_hooks("set theme='default-dark'")
    # prevent the system call for the edit
    mock_os_system = mocker.patch("os.system")
    # and make sure we can't apply the theme
    apply_mock = mocker.patch("tomcatmanager.InteractiveTomcatManager._apply_theme")
    apply_mock.return_value = False
    itm_nc.onecmd_plus_hooks("theme edit")
    # but let's check to make sure the editor was called
    assert mock_os_system.call_count == 1
    # we don't check error messages, because those all get generated in _apply_theme
    # but we should have an error for our exit code
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR


def test_theme_clone_from_gallery(itm_nc, tmp_path, mocker, response_with):
    # mock a theme coming from the gallery
    theme_name = "mockedtheme"
    theme_str = """
    description="noop"
    """
    response = response_with(200, theme_str)
    get_mock = mocker.patch("requests.get", return_value=response)
    # patch the user theme dir
    theme_dir_mock = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
        new_callable=mock.PropertyMock,
    )
    theme_dir_mock.return_value = tmp_path

    itm_nc.onecmd_plus_hooks(f"theme clone {theme_name}")
    assert get_mock.call_count == 1
    new_theme_path = tmp_path / f"{theme_name}.toml"
    assert new_theme_path.is_file()


def test_theme_clone_unknown(itm_nc, tmp_path, mocker, response_with):
    # mock no theme in the gallery
    theme_name = "unknowntheme"
    response = response_with(404, "")
    get_mock = mocker.patch("requests.get", return_value=response)
    # patch the user theme dir
    theme_dir_mock = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
        new_callable=mock.PropertyMock,
    )
    theme_dir_mock.return_value = tmp_path

    itm_nc.onecmd_plus_hooks(f"theme clone {theme_name}")
    assert get_mock.call_count == 1
    new_theme_path = tmp_path / f"{theme_name}.toml"
    assert not new_theme_path.is_file()


def test_theme_clone_wont_overwrite(itm_nc, capsys, tmp_path, mocker, response_with):
    # mock no theme in the gallery
    theme_name = "default-dark"
    response = response_with(404, "")
    get_mock = mocker.patch("requests.get", return_value=response)
    # patch the user theme dir
    theme_dir_mock = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
        new_callable=mock.PropertyMock,
    )
    theme_dir_mock.return_value = tmp_path
    # write a theme with the name into the user theme dir
    new_theme_path = tmp_path / f"{theme_name}.toml"
    with open(new_theme_path, "w", encoding="utf-8"):
        pass

    itm_nc.onecmd_plus_hooks(f"theme clone {theme_name}")
    out, err = capsys.readouterr()
    assert get_mock.call_count == 1
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR
    assert not out
    assert "clone aborted" in err


def test_theme_create(itm_nc, capsys, tmp_path, mocker):
    theme_name = "mynewtheme"
    # patch the user theme dir
    theme_dir_mock = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
        new_callable=mock.PropertyMock,
    )
    theme_dir_mock.return_value = tmp_path

    itm_nc.onecmd_plus_hooks(f"theme create {theme_name}")
    out, err = capsys.readouterr()
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS
    assert not out
    assert "copying theme template" in err
    new_theme_path = tmp_path / f"{theme_name}.toml"
    assert new_theme_path.is_file()


def test_theme_create_already_exist(itm_nc, capsys, tmp_path, mocker):
    theme_name = "mynewtheme"
    # patch the user theme dir
    theme_dir_mock = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
        new_callable=mock.PropertyMock,
    )
    theme_dir_mock.return_value = tmp_path
    # write a theme with the name into the user theme dir
    new_theme_path = tmp_path / f"{theme_name}.toml"
    with open(new_theme_path, "w", encoding="utf-8"):
        pass

    itm_nc.onecmd_plus_hooks(f"theme create {theme_name}")
    out, err = capsys.readouterr()
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR
    assert not out
    assert "create aborted" in err


def test_theme_create_no_template(itm_nc, capsys, tmp_path, mocker):
    theme_name = "mynewtheme"
    # patch the user theme dir
    theme_dir_mock = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
        new_callable=mock.PropertyMock,
    )
    theme_dir_mock.return_value = tmp_path
    # prevent the theme template from being copied
    shcopy_mock = mocker.patch("shutil.copy")
    shcopy_mock.side_effect = FileNotFoundError()

    itm_nc.onecmd_plus_hooks(f"theme create {theme_name}")
    out, err = capsys.readouterr()
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS
    assert not out
    assert "copying theme template" in err
    new_theme_path = tmp_path / f"{theme_name}.toml"
    assert new_theme_path.is_file()


def test_theme_delete(itm_nc, capsys, tmp_path, mocker):
    theme_name = "mynewtheme"
    # patch the user theme dir
    theme_dir_mock = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
        new_callable=mock.PropertyMock,
    )
    theme_dir_mock.return_value = tmp_path
    # write a theme with the name into the user theme dir
    new_theme_path = tmp_path / f"{theme_name}.toml"
    with open(new_theme_path, "w", encoding="utf-8"):
        pass
    # mock up standard input for the "are you sure?" prompt
    mock_input = mocker.patch("builtins.input")
    mock_input.return_value = "yes"

    itm_nc.onecmd_plus_hooks(f"theme delete {theme_name}")
    out, err = capsys.readouterr()
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS
    assert "theme deleted" in err
    assert not out
    assert not new_theme_path.is_file()


def test_theme_delete_no_confirm(itm_nc, capsys, tmp_path, mocker):
    theme_name = "mynewtheme"
    # patch the user theme dir
    theme_dir_mock = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
        new_callable=mock.PropertyMock,
    )
    theme_dir_mock.return_value = tmp_path
    # write a theme with the name into the user theme dir
    new_theme_path = tmp_path / f"{theme_name}.toml"
    with open(new_theme_path, "w", encoding="utf-8"):
        pass
    # mock up standard input for the "are you sure?" prompt
    mock_input = mocker.patch("builtins.input")
    mock_input.return_value = "no"

    itm_nc.onecmd_plus_hooks(f"theme delete {theme_name}")
    out, err = capsys.readouterr()
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR
    assert "no confirmation" in err
    assert not out
    assert new_theme_path.is_file()


def test_theme_delete_force(itm_nc, capsys, tmp_path, mocker):
    theme_name = "mynewtheme"
    # patch the user theme dir
    theme_dir_mock = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
        new_callable=mock.PropertyMock,
    )
    theme_dir_mock.return_value = tmp_path
    # write a theme with the name into the user theme dir
    new_theme_path = tmp_path / f"{theme_name}.toml"
    with open(new_theme_path, "w", encoding="utf-8"):
        pass

    itm_nc.onecmd_plus_hooks(f"theme delete -f {theme_name}")
    out, err = capsys.readouterr()
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS
    assert "theme deleted" in err
    assert not out
    assert not new_theme_path.is_file()


def test_theme_delete_unknown(itm_nc, capsys, tmp_path, mocker):
    theme_name = "mynewtheme"
    # patch the user theme dir
    theme_dir_mock = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
        new_callable=mock.PropertyMock,
    )
    theme_dir_mock.return_value = tmp_path

    itm_nc.onecmd_plus_hooks(f"theme delete {theme_name}")
    out, err = capsys.readouterr()
    assert itm_nc.exit_code == itm_nc.EXIT_ERROR
    assert "unknown theme" in err
    assert not out


###
#
# miscellaneous commands
#
###
def test_exit(itm_nc):
    itm_nc.onecmd_plus_hooks("exit")
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_quit(itm_nc):
    itm_nc.onecmd_plus_hooks("quit")
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS


def test_exit_code(itm_nc, capsys):
    itm_nc.onecmd_plus_hooks("version")
    out, _ = capsys.readouterr()
    itm_nc.onecmd_plus_hooks("exit_code")
    out, _ = capsys.readouterr()
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS
    assert out == f"{itm_nc.EXIT_SUCCESS}\n"


def test_version(itm_nc, capsys):
    itm_nc.onecmd_plus_hooks("version")
    out, _ = capsys.readouterr()
    assert itm_nc.exit_code == itm_nc.EXIT_SUCCESS
    assert tm.__version__ in out


def test_default(itm_nc, capsys):
    cmdline = "notacommand"
    itm_nc.onecmd_plus_hooks(cmdline)
    out, err = capsys.readouterr()
    assert itm_nc.exit_code == itm_nc.EXIT_COMMAND_NOT_FOUND
    assert not out
    assert err == f"unknown command: {cmdline}\n"


def test_license(itm_nc, capsys):
    itm_nc.onecmd_plus_hooks("license")
    out, _ = capsys.readouterr()
    expected = textwrap.dedent(
        """\
        Copyright 2007 Jared Crapo

        Permission is hereby granted, free of charge, to any person obtaining a
        copy of this software and associated documentation files (the "Software"),
        to deal in the Software without restriction, including without limitation
        the rights to use, copy, modify, merge, publish, distribute, sublicense,
        and/or sell copies of the Software, and to permit persons to whom the
        Software is furnished to do so, subject to the following conditions:

        The above copyright notice and this permission notice shall be included in
        all copies or substantial portions of the Software.

        THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
        IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
        FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
        AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
        LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
        FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
        DEALINGS IN THE SOFTWARE.

        """
    )
    assert out == expected


###
#
# test Theme model from InteractiveTomcatManager
#
###
def test_theme_empty():
    thm = tm.interactive_tomcat_manager.Theme()
    assert not thm.file
    assert not thm.name


###
#
# other tests
#
###
def test_thrown_exception(itm, mocker, capsys):
    itm.exit_code = itm.EXIT_SUCCESS
    raise_mock = mocker.patch(
        "tomcatmanager.models.TomcatManagerResponse.raise_for_status"
    )
    raise_mock.side_effect = tm.TomcatError()
    itm.onecmd_plus_hooks("serverinfo")
    _, err = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_ERROR
    assert err
