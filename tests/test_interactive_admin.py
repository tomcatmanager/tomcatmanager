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
    import importlib_resources

import pathlib
import tempfile
import textwrap
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
def get_itm(tms):
    """
    Using this as a fixture with capsys breaks capsys. So we use a function.
    """
    itm = tm.InteractiveTomcatManager(loadconfig=False)
    itm.onecmd_plus_hooks(tms.connect_command)
    return itm


def itm_with_config(mocker, configstring):
    """Return an InteractiveTomcatManager object with the config set from the passed string."""

    # prevent notification of conversion from old to new format
    mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.config_file_old",
        new_callable=mock.PropertyMock,
        return_value=None,
    )

    # create an interactive tomcat manager object
    itm = tm.InteractiveTomcatManager(loadconfig=False)
    # write the passed string to a temp file
    with tempfile.TemporaryDirectory() as tmpdir:
        configfile = pathlib.Path(tmpdir) / "tomcat-manager.toml"
        with open(configfile, "w", encoding="utf-8") as fobj:
            fobj.write(configstring)

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
    "theme invalid",
    "expire",
    "expire /tmp/somepath",
]


@pytest.mark.parametrize("command", USAGE_COMMANDS)
def test_command_usage(tomcat_manager_server, command):
    itm = get_itm(tomcat_manager_server)
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
def test_command_help(tomcat_manager_server, command):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.EXIT_ERROR
    itm.onecmd_plus_hooks(f"{command} -h")
    assert itm.exit_code == itm.EXIT_USAGE

    itm.exit_code = itm.EXIT_ERROR
    itm.onecmd_plus_hooks(f"{command} --help")
    assert itm.exit_code == itm.EXIT_USAGE


# copy the list
HELP_ARGPARSERS = list(HELP_COMMANDS)
# there is an argparser for exit_code, but it's only used
# to generate the help
HELP_ARGPARSERS.append("exit_code")


@pytest.mark.parametrize("command", HELP_ARGPARSERS)
def test_help_matches_argparser(command, capsys):
    itm = tm.InteractiveTomcatManager()
    cmdline = f"help {command}"
    itm.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    parser_func = getattr(itm, f"{command}_parser")
    assert out.strip() == parser_func.format_help().strip()
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_help_set(capsys):
    # set gets it's own testing mechanism because it doesn't use argparser
    # it needs to preserve quotes and such so toml parsing works as expected
    itm = tm.InteractiveTomcatManager()
    cmdline = "help set"
    itm.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "change a program setting" in out
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_help_deploy_local(capsys):
    itm = tm.InteractiveTomcatManager()
    cmdline = "help deploy local"
    itm.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "local file system" in out
    assert "warfile" in out
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_help_deploy_server(capsys):
    itm = tm.InteractiveTomcatManager()
    cmdline = "help deploy server"
    itm.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "server file system" in out
    assert "warfile" in out
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_help_deploy_context(capsys):
    itm = tm.InteractiveTomcatManager()
    cmdline = "help deploy context"
    itm.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "server file system" in out
    assert "warfile" in out
    assert "contextfile" in out
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_help_deploy_invalid(capsys):
    itm = tm.InteractiveTomcatManager()
    cmdline = "help deploy invalid"
    itm.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "deployment_method" in out
    assert "local" in out
    assert "server" in out
    assert "context" in out
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_help_theme_list(capsys):
    itm = tm.InteractiveTomcatManager()
    cmdline = "help theme list"
    itm.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "list all themes" in out
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_help_theme_clone(capsys):
    itm = tm.InteractiveTomcatManager()
    cmdline = "help theme clone"
    itm.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "clone a theme" in out
    assert "name" in out
    assert "new_name" in out
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_help_theme_edit(capsys):
    itm = tm.InteractiveTomcatManager()
    cmdline = "help theme edit"
    itm.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "edit a user theme" in out
    assert "name" in out
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_help_theme_create(capsys):
    itm = tm.InteractiveTomcatManager()
    cmdline = "help theme create"
    itm.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "create a new user theme" in out
    assert "name" in out
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_help_theme_delete(capsys):
    itm = tm.InteractiveTomcatManager()
    cmdline = "help theme delete"
    itm.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "delete a user theme" in out
    assert "name" in out
    assert "--force" in out
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_help_theme_dir(capsys):
    itm = tm.InteractiveTomcatManager()
    cmdline = "help theme dir"
    itm.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "theme directory" in out
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_help_theme_invalid(capsys):
    itm = tm.InteractiveTomcatManager()
    cmdline = "help theme invalid"
    itm.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "manage themes" in out
    assert "list" in out
    assert "dir" in out
    assert "create" in out
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_help(capsys):
    itm = tm.InteractiveTomcatManager()
    cmdline = "help"
    itm.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "Connecting to a Tomcat server" in out
    assert "Managing applications" in out
    assert "Server information" in out
    assert "Settings, configuration, and tools" in out
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_help_invalid(capsys):
    itm = tm.InteractiveTomcatManager()
    cmdline = "help invalidcommand"
    itm.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_ERROR


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
def test_convert_to_boolean_valid(param, value):
    itm = tm.InteractiveTomcatManager()
    assert itm.convert_to_boolean(param) == value


NOT_BOOLEANS = [
    None,
    "",
    10,
    "ace",
]


@pytest.mark.parametrize("param", NOT_BOOLEANS)
def test_convert_to_boolean_invalid(param):
    itm = tm.InteractiveTomcatManager()
    with pytest.raises(ValueError):
        itm.convert_to_boolean(param)


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


def test_config_edit(itm, mocker):
    itm.editor = "fooedit"
    mock_os_system = mocker.patch("os.system")
    itm.onecmd_plus_hooks("config edit")
    assert mock_os_system.call_count == 1
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_config_edit_no_editor(itm, capsys):
    itm.editor = None
    itm.onecmd_plus_hooks("config edit")
    out, err = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_ERROR
    assert not out
    assert err.startswith("no editor: ")


def test_config_invalid_action(itm, capsys):
    itm.onecmd_plus_hooks("config bogus")
    out, err = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_USAGE
    assert not out
    assert err.startswith("usage: ")


def test_config_file_command(mocker, capsys):
    fname = pathlib.Path("/tmp/someconfig.ini")
    itm = tm.InteractiveTomcatManager()

    config_file = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.config_file",
        new_callable=mock.PropertyMock,
    )
    config_file.return_value = str(fname)

    itm.onecmd_plus_hooks("config file")
    out, _ = capsys.readouterr()
    assert out == f"{str(fname)}\n"
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_config_convert_no_config(mocker, capsys):
    # verify conversion behavior when neither ini nor toml config files exist
    itm = tm.InteractiveTomcatManager()

    with tempfile.TemporaryDirectory() as tmpdir:
        inifile = pathlib.Path(tmpdir) / "tomcat-manager.ini"
        tomlfile = pathlib.Path(tmpdir) / "tomcat-manager.toml"

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

        itm.onecmd_plus_hooks("config convert")
        _, err = capsys.readouterr()

        assert "old configuration file does not exist: nothing to convert" in err
        assert itm.exit_code == itm.EXIT_ERROR


def test_config_convert(mocker, capsys):
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

    itm = tm.InteractiveTomcatManager(loadconfig=False)

    with tempfile.TemporaryDirectory() as tmpdir:
        inifile = pathlib.Path(tmpdir) / "tomcat-manager.ini"
        tomlfile = pathlib.Path(tmpdir) / "tomcat-manager.toml"

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

        itm.onecmd_plus_hooks("config convert")
        _, err = capsys.readouterr()

        assert "converting old configuration file to new format" in err
        assert "reloading configuration" in err
        assert itm.exit_code == itm.EXIT_SUCCESS

        with open(tomlfile, "r", encoding="utf-8") as tomlobj:
            test_tomlconfig = tomlobj.read()
            assert test_tomlconfig == tomlconfig


def test_config_convert_invalid_setting(mocker, capsys):
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

    itm = tm.InteractiveTomcatManager()

    with tempfile.TemporaryDirectory() as tmpdir:
        inifile = pathlib.Path(tmpdir) / "tomcat-manager.ini"
        tomlfile = pathlib.Path(tmpdir) / "tomcat-manager.toml"

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

        itm.onecmd_plus_hooks("config convert")
        _, err = capsys.readouterr()

        assert "converting old configuration file to new format" in err
        assert "conversion failed" in err
        assert itm.exit_code == itm.EXIT_ERROR


def test_config_convert_both_exist(mocker, capsys):
    itm = tm.InteractiveTomcatManager()

    with tempfile.TemporaryDirectory() as tmpdir:
        inifile = pathlib.Path(tmpdir) / "tomcat-manager.ini"
        inifile.touch()
        tomlfile = pathlib.Path(tmpdir) / "tomcat-manager.toml"
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

        itm.onecmd_plus_hooks("config convert")
        _, err = capsys.readouterr()

        assert "configuration file exists: cowardly refusing to overwrite it" in err
        assert itm.exit_code == itm.EXIT_ERROR


def test_load_config(mocker):
    prompt = str(uuid.uuid1())
    configstring = f"""
        [settings]
        prompt = "{prompt}"
        """
    itm = itm_with_config(mocker, configstring)
    assert itm.prompt == prompt


def test_load_config_file_not_found():
    with mock.patch("builtins.open", mock.mock_open()) as mocked_open:
        mocked_open.side_effect = FileNotFoundError()
        itm = tm.InteractiveTomcatManager()
        assert len(itm.config.keys()) == 0


def test_load_config_bogus_setting(mocker):
    configstring = """
        [settings]
        bogus = true
        """
    # this shouldn't throw any exceptions
    itm_with_config(mocker, configstring)


def test_load_config_not_boolean(itm, mocker):
    configstring = """
        [settings]
        echo = "not a boolean"
        """
    # this shouldn't throw any exceptions
    itm = itm_with_config(mocker, configstring)
    # make sure the echo setting is the same
    # as when we don't load a config file
    assert itm.echo == itm.echo


def test_load_config_echo_false(mocker):
    configstring = """
        [settings]
        echo = false
        """
    # this shouldn't throw any exceptions
    itm = itm_with_config(mocker, configstring)
    # make sure the echo setting is the same
    # as when we don't load a config file
    assert itm.echo is False


def test_load_config_echo_true(mocker):
    configstring = """
        [settings]
        echo = true
        """
    # this shouldn't throw any exceptions
    itm = itm_with_config(mocker, configstring)
    # make sure the echo setting is the same
    # as when we don't load a config file
    assert itm.echo is True


def test_load_config_not_integer(itm, mocker):
    configstring = """
        [settings]
        timeout = "notaninteger"
        """
    # this shouldn't throw any exceptions
    itm = itm_with_config(mocker, configstring)
    # make sure the timeout setting is the same
    # as when we don't load a config file
    assert itm.timeout == itm.timeout


def test_load_config_syntax_error(itm, mocker, capsys):
    configstring = """
        [settings]
        prompt = "tm>
        """
    itm = itm_with_config(mocker, configstring)
    out, err = capsys.readouterr()
    assert "error loading configuration file" in err
    # make sure that loading the broken configuration file didn't
    # change the prompt
    assert itm.prompt == itm.prompt


def test_show_invalid(capsys):
    # make sure that the show command, which we have overridden, doesn't
    # do the thing that it does by default in cmd2.Cmd
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks("show")
    out, err = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_COMMAND_NOT_FOUND
    assert not out
    assert "unknown command: show" in err


def test_settings_noargs(capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks("settings")
    out, _ = capsys.readouterr()
    # make sure there is a line for each setting
    assert len(out.splitlines()) == len(itm.settables)
    # check the first setting is "debug", they are sorted in
    # alphabetical order, so this one should come out first
    assert out.splitlines()[0].split("=")[0].strip() == "debug"
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_settings_valid_setting(capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks("settings prompt")
    out, _ = capsys.readouterr()
    assert out.startswith(f'prompt = "{itm.prompt}" ')
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_settings_invalid_setting(capsys):
    itm = tm.InteractiveTomcatManager()
    itm.debug = False
    itm.onecmd_plus_hooks("settings bogus")
    out, err = capsys.readouterr()
    assert not out
    assert err == "unknown setting: 'bogus'\n"
    assert itm.exit_code == itm.EXIT_ERROR


def test_set_noargs(capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks("set")
    out, _ = capsys.readouterr()
    # make sure there is a line for each setting
    assert len(out.splitlines()) == len(itm.settables)
    # check the first setting is "debug", they are sorted in
    # alphabetical order, so this one should come out first
    assert out.splitlines()[0].split("=")[0].strip() == "debug"
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_set_help(capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks("set -h")
    out, _ = capsys.readouterr()
    assert "change a program setting" in out
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_set_string():
    itm = tm.InteractiveTomcatManager()
    prompt = str(uuid.uuid1())
    itm.onecmd_plus_hooks(f"set prompt = '{prompt}'")
    assert itm.prompt == prompt
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_set_mismatched_quotes(capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks("set prompt = notquoted")
    _, err = capsys.readouterr()
    assert "invalid syntax" in err
    assert itm.exit_code == itm.EXIT_ERROR


def test_set_quiet_to_string_nodebug(capsys):
    itm = tm.InteractiveTomcatManager()
    itm.debug = False
    itm.onecmd_plus_hooks('set debug = "shouldbeboolean"')
    _, err = capsys.readouterr()
    # it would be nice if we could check what the error message is, but
    # it's generated by CMD, so we don't get to control when it changes
    assert err
    assert itm.exit_code == itm.EXIT_ERROR


def test_set_quiet_to_string_debug(capsys):
    itm = tm.InteractiveTomcatManager()
    itm.debug = True
    itm.onecmd_plus_hooks('set debug = "shouldbeboolean"')
    _, err = capsys.readouterr()
    # it would be nice if we could check what the error message is, but
    # it's generated by CMD, so we don't get to control when it changes
    assert err
    assert itm.exit_code == itm.EXIT_ERROR


def test_set_float_valid():
    itm = tm.InteractiveTomcatManager()
    itm.timeout = 10.0
    itm.onecmd_plus_hooks("set timeout = 5.5")
    assert itm.timeout == 5.5
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_set_float_invalid():
    itm = tm.InteractiveTomcatManager()
    itm.debug = False
    itm.timeout = 10.0
    itm.onecmd_plus_hooks("set timeout = joe")
    assert itm.timeout == 10.0
    assert itm.exit_code == itm.EXIT_ERROR


def test_set_float_invalid_debug():
    itm = tm.InteractiveTomcatManager()
    itm.debug = True
    itm.timeout = 10.0
    itm.onecmd_plus_hooks("set timeout = joe")
    assert itm.timeout == 10.0
    assert itm.exit_code == itm.EXIT_ERROR


def test_set_boolean_true():
    itm = tm.InteractiveTomcatManager()
    itm.echo = False
    itm.onecmd_plus_hooks("set echo = true")
    assert itm.echo is True
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_set_boolean_false():
    itm = tm.InteractiveTomcatManager()
    itm.echo = True
    itm.onecmd_plus_hooks("set echo = false")
    assert itm.echo is False
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_set_boolean_invalid():
    itm = tm.InteractiveTomcatManager()
    itm.echo = False
    itm.onecmd_plus_hooks("set echo = notaboolean")
    assert itm.echo is False
    assert itm.exit_code == itm.EXIT_ERROR


def test_set_boolean_zero():
    itm = tm.InteractiveTomcatManager()
    itm.echo = True
    itm.onecmd_plus_hooks("set echo = 0")
    assert itm.echo is False
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_set_debug_invalid():
    itm = tm.InteractiveTomcatManager()
    itm.echo = False
    itm.debug = True
    itm.onecmd_plus_hooks("set echo = notaboolean")
    assert itm.echo is False
    assert itm.exit_code == itm.EXIT_ERROR


def test_set_unknown_setting(capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks("set fred = 'somevalue'")
    _, err = capsys.readouterr()
    assert "unknown setting" in err
    assert itm.exit_code == itm.EXIT_ERROR


def test_set_with_invalid_param():
    itm = tm.InteractiveTomcatManager()
    # this uuid won't be in itm.settables
    invalid_setting = str(uuid.uuid1())
    with pytest.raises(ValueError):
        # pylint: disable=protected-access
        itm._change_setting(invalid_setting, "someval")


def test_timeout_property():
    timeout = 8.5
    itm = tm.InteractiveTomcatManager()
    # set this to a value that we know will cause it to change when we execute
    # the command
    itm.timeout = 5
    assert itm.tomcat.timeout == 5
    itm.onecmd_plus_hooks(f"set timeout = {timeout}")
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert itm.timeout == timeout
    assert itm.tomcat.timeout == timeout


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
def test_do_set_success(arg, value):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks(arg)
    assert itm.prompt == value
    assert itm.exit_code == itm.EXIT_SUCCESS


SETTINGS_FAILURE = [
    "set thisisntaparam=somevalue",
    "set thisisntaparam",
]


@pytest.mark.parametrize("arg", SETTINGS_FAILURE)
def test_do_set_fail(arg):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks(arg)
    assert itm.exit_code == itm.EXIT_ERROR


PREFIXES = [
    ("--", "--"),
    ("*", "*"),
    (">>>", ">>>"),
    # with no prefix, we should see the connected message
    ("", "connect"),
]


@pytest.mark.parametrize("prefix, expected", PREFIXES)
def test_status_prefix(tomcat_manager_server, itm, prefix, expected, capsys):
    itm.status_prefix = prefix
    itm.quiet = False
    itm.onecmd_plus_hooks(tomcat_manager_server.connect_command)
    out, err = capsys.readouterr()
    assert err.startswith(expected)
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_status_animation():
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks("set status_animation = 'dots'")
    assert itm.status_animation == "dots"
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_status_animation_invalid(capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks("set status_animation = 'invalid'")
    _, err = capsys.readouterr()
    assert "invalid" in err
    assert itm.exit_code == itm.EXIT_ERROR


def test_status_animation_none():
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks("set status_animation = ''")
    assert itm.status_animation == ""
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_theme_default_none():
    itm = tm.InteractiveTomcatManager(loadconfig=False)
    assert itm.theme == ""


def test_theme_use_embedded(mocker):
    itm = tm.InteractiveTomcatManager(loadconfig=False)
    theme = "default-dark"
    with tempfile.TemporaryDirectory() as tmpdir:
        # patch the empty temporary directory into user_theme_dir
        # to make sure we are loading the built-in theme
        tmppath = pathlib.Path(tmpdir)
        mocker.patch(
            "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
            new_callable=mock.PropertyMock,
            return_value=tmppath,
        )
        itm.onecmd_plus_hooks(f"set theme = '{theme}'")
        assert itm.theme == theme


def test_theme_invalid(capsys):
    itm = tm.InteractiveTomcatManager(loadconfig=False)
    theme = str(uuid.uuid1())
    assert not itm.theme
    itm.onecmd_plus_hooks(f"set theme = '{theme}'")
    out, err = capsys.readouterr()
    assert not itm.theme
    assert err
    assert not out


def test_resolve_theme_builtin(mocker):
    itm = tm.InteractiveTomcatManager(loadconfig=False)
    # this is one of our builtin themes
    theme_name = "default-dark"
    with tempfile.TemporaryDirectory() as tmpdir:
        # patch the empty temporary directory into user_theme_dir
        # this avoids the test failing if the user running the test
        # happens to have cloned one of the built-in themes
        tmppath = pathlib.Path(tmpdir)
        mocker.patch(
            "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
            new_callable=mock.PropertyMock,
            return_value=tmppath,
        )
        location, path = itm._resolve_theme(theme_name)
        assert location == tm.interactive_tomcat_manager.ThemeLocation.BUILTIN
        assert path
        assert str(importlib_resources.files("tomcatmanager.themes")) in str(path)
        assert theme_name in str(path)


def test_resolve_theme_invalid_name():
    itm = tm.InteractiveTomcatManager(loadconfig=False)
    # shouldn't find this random uuid as a theme
    theme = str(uuid.uuid1())
    location, path = itm._resolve_theme(theme)
    assert not location
    assert not path


def test_resolve_theme_user(mocker, capsys):
    itm = tm.InteractiveTomcatManager(loadconfig=False)
    theme = str(uuid.uuid1())
    # get a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # write a simple theme file into the directory
        tmppath = pathlib.Path(tmpdir)
        themefile = tmppath / f"{theme}.toml"
        with open(themefile, "w", encoding="utf-8") as file_var:
            file_var.write("tm.error = 'red'\n")
        # patch the temporary directory into user_theme_dir
        mocker.patch(
            "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
            new_callable=mock.PropertyMock,
            return_value=tmppath,
        )
        # now that we are all set up, go try and load the theme
        itm.onecmd_plus_hooks(f"set theme = '{theme}'")
        out, err = capsys.readouterr()
        errarray = err.rstrip("\n").split("\n")
        assert len(errarray) == 1
        assert "skipping load of configuration file" in errarray[0]
        assert not out
        assert itm.theme == theme


def test_user_theme_dir():
    itm = tm.InteractiveTomcatManager(loadconfig=False)
    assert "themes" in str(itm.user_theme_dir)
    # if appdirs doesn't exist, config_file shouldn't either
    itm.appdirs = None
    assert not itm.user_theme_dir


def test_apply_theme_file_parse_error(mocker, capsys):
    theme = "someusertheme"
    itm = tm.InteractiveTomcatManager(loadconfig=False)
    # get a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # write a theme file with a syntax error
        tmppath = pathlib.Path(tmpdir)
        themefile = tmppath / f"{theme}.toml"
        with open(themefile, "w", encoding="utf-8") as file_var:
            file_var.write("tm.error = 'red\n")
        # patch the temporary directory into user_theme_dir
        mocker.patch(
            "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
            new_callable=mock.PropertyMock,
            return_value=tmppath,
        )
        # now that we are all set up, go try and load the theme
        itm.onecmd_plus_hooks(f"set theme = '{theme}'")
        out, err = capsys.readouterr()
        assert err
        assert not out
        assert not itm.theme
        assert itm.theme == ""


def test_apply_theme_permission_error(mocker, capsys):
    theme = "someusertheme"
    itm = tm.InteractiveTomcatManager(loadconfig=False)
    # get a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # write a theme file with a syntax error
        tmppath = pathlib.Path(tmpdir)
        themefile = tmppath / f"{theme}.toml"
        with open(themefile, "w", encoding="utf-8") as file_var:
            file_var.write("tm.error = 'red'\n")
        # patch the temporary directory into user_theme_dir
        mocker.patch(
            "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
            new_callable=mock.PropertyMock,
            return_value=tmppath,
        )
        # patch open to throw a permission error
        with mock.patch("builtins.open", mock.mock_open()) as mocked_open:
            mocked_open.side_effect = PermissionError()
            # now that we are all set up, go try and load the theme
            itm.onecmd_plus_hooks(f"set theme = '{theme}'")
            out, err = capsys.readouterr()
            assert err
            assert not out
            assert not itm.theme


def test_apply_theme_invalid_theme_color(mocker, capsys):
    theme = "someusertheme"
    itm = tm.InteractiveTomcatManager(loadconfig=False)
    # get a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # write a theme file with a syntax error
        tmppath = pathlib.Path(tmpdir)
        themefile = tmppath / f"{theme}.toml"
        with open(themefile, "w", encoding="utf-8") as file_var:
            file_var.write("tm.error = 'dodget_blue2'\n")
        # patch the temporary directory into user_theme_dir
        mocker.patch(
            "tomcatmanager.InteractiveTomcatManager.user_theme_dir",
            new_callable=mock.PropertyMock,
            return_value=tmppath,
        )
        # now that we are all set up, go try and load the theme
        itm.onecmd_plus_hooks(f"set theme = '{theme}'")
        out, err = capsys.readouterr()
        assert err
        assert not out
        assert not itm.theme
        assert itm.theme == ""


###
#
# miscellaneous commands
#
###
def test_exit():
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks("exit")
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_quit():
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks("quit")
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_exit_code(capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks("version")
    out, _ = capsys.readouterr()
    itm.onecmd_plus_hooks("exit_code")
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert out == f"{itm.EXIT_SUCCESS}\n"


def test_version(capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks("version")
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert tm.__version__ in out


def test_default(capsys):
    cmdline = "notacommand"
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks(cmdline)
    out, err = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_COMMAND_NOT_FOUND
    assert not out
    assert err == f"unknown command: {cmdline}\n"


def test_license(capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks("license")
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
# other tests
#
###
def test_thrown_exception(tomcat_manager_server, mocker, capsys):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.EXIT_SUCCESS
    raise_mock = mocker.patch(
        "tomcatmanager.models.TomcatManagerResponse.raise_for_status"
    )
    raise_mock.side_effect = tm.TomcatError()
    itm.onecmd_plus_hooks("serverinfo")
    _, err = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_ERROR
    assert err
