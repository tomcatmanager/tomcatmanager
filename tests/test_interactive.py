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

import os
import tempfile
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
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks(tms.connect_command)
    return itm


def itm_with_config(mocker, configstring):
    """Return an InteractiveTomcatManager object with the config set from the passed string."""
    itm = tm.InteractiveTomcatManager()
    fdesc, fname = tempfile.mkstemp(prefix="", suffix=".ini")
    os.close(fdesc)
    with open(fname, "w", encoding="utf-8") as fobj:
        fobj.write(configstring)

    # itm aleady tried to load a config file, which it may or may not
    # have found, depending on if you have one or not
    # we are now going to patch up the config_file to point to
    # a known file, and the reload the config from that
    try:
        config_file = mocker.patch(
            "tomcatmanager.InteractiveTomcatManager.config_file",
            new_callable=mock.PropertyMock,
        )
        config_file.return_value = fname
        itm.load_config()
        # this just verifies that our patch worked
        assert itm.config_file == fname
    finally:
        os.remove(fname)
    return itm


def assert_connected_to(itm, url, capsys):
    itm.onecmd_plus_hooks("which")
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert url in out


@pytest.fixture
def itm_nc(mocker):
    """Don't allow it to load a config file"""
    mocker.patch("tomcatmanager.InteractiveTomcatManager.load_config", autospec=True)
    itm = tm.InteractiveTomcatManager()
    return itm


###
#
# test help
#
###
HELP_COMMANDS = [
    "config",
    "show",
    "settings",
    "connect",
    "which",
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
    itm.onecmd_plus_hooks("{} -h".format(command))
    assert itm.exit_code == itm.EXIT_USAGE

    itm.exit_code = itm.EXIT_ERROR
    itm.onecmd_plus_hooks("{} --help".format(command))
    assert itm.exit_code == itm.EXIT_USAGE


# copy the list
HELP_ARGPARSERS = list(HELP_COMMANDS)
# there is an argparser for exit_code, but it's only used
# to generate the help
HELP_ARGPARSERS.append("exit_code")


@pytest.mark.parametrize("command", HELP_ARGPARSERS)
def test_help_matches_argparser(command, capsys):
    itm = tm.InteractiveTomcatManager()
    cmdline = "help {}".format(command)
    itm.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    parser_func = getattr(itm, "{}_parser".format(command))
    assert out == parser_func.format_help()
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_help_set(capsys):
    itm = tm.InteractiveTomcatManager()
    cmdline = "help set"
    itm.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert "change the value of one of this program's settings" in out
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


def test_config_invalid_action(itm_nc, capsys):
    itm_nc.onecmd_plus_hooks("config bogus")
    out, err = capsys.readouterr()
    assert itm_nc.exit_code == itm_nc.EXIT_USAGE
    assert not out
    assert err.startswith("usage: ")


def test_config_file_command(mocker, capsys):
    fname = "/tmp/someconfig.ini"
    itm = tm.InteractiveTomcatManager()

    config_file = mocker.patch(
        "tomcatmanager.InteractiveTomcatManager.config_file",
        new_callable=mock.PropertyMock,
    )
    config_file.return_value = fname

    itm.onecmd_plus_hooks("config file")
    out, _ = capsys.readouterr()
    assert out == "{}\n".format(fname)
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_load_config(mocker):
    prompt = str(uuid.uuid1())
    configstring = "[settings]\nprompt={}\n".format(prompt)
    itm = itm_with_config(mocker, configstring)
    assert itm.prompt == prompt


def test_load_config_file_not_found():
    with mock.patch("builtins.open", mock.mock_open()) as mocked_open:
        mocked_open.side_effect = FileNotFoundError()
        itm = tm.InteractiveTomcatManager()
        assert len(itm.config.sections()) == 0


def test_load_config_bogus_setting(mocker):
    configstring = "[settings]\nbogus=True\n"
    # this shouldn't throw any exceptions
    itm_with_config(mocker, configstring)


def test_load_config_not_boolean(itm_nc, mocker):
    configstring = '[settings]\necho="not a boolean"\n'
    # this shouldn't throw any exceptions
    itm = itm_with_config(mocker, configstring)
    # make sure the echo setting is the same
    # as when we don't load a config file
    assert itm_nc.echo == itm.echo


def test_load_config_not_integer(itm_nc, mocker):
    configstring = "[settings]\ntimeout=noganinteger\n"
    # this shouldn't throw any exceptions
    itm = itm_with_config(mocker, configstring)
    # make sure the timeout setting is the same
    # as when we don't load a config file
    assert itm_nc.timeout == itm.timeout


SHOW_SETTINGS = ["settings", "show"]


@pytest.mark.parametrize("command", SHOW_SETTINGS)
def test_show_noargs(command, capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks(command)
    out, _ = capsys.readouterr()
    # not going to parse all the lines, but there
    # should be one per setting
    assert len(out.splitlines()) == len(itm.settables)
    assert itm.exit_code == itm.EXIT_SUCCESS


@pytest.mark.parametrize("command", SHOW_SETTINGS)
def test_show_valid_setting(command, capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks("{} prompt".format(command))
    out, _ = capsys.readouterr()
    assert out.startswith("prompt='{}' ".format(itm.prompt))
    assert itm.exit_code == itm.EXIT_SUCCESS


@pytest.mark.parametrize("command", SHOW_SETTINGS)
def test_show_invalid_setting(command, capsys):
    itm = tm.InteractiveTomcatManager()
    itm.debug = False
    itm.onecmd_plus_hooks("{} bogus".format(command))
    out, err = capsys.readouterr()
    assert not out
    assert err == "unknown setting: 'bogus'\n"
    assert itm.exit_code == itm.EXIT_ERROR


def test_set_noargs(capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks("set")
    out, err = capsys.readouterr()
    assert not out
    assert err == "invalid syntax: try {setting}={value}\n"
    assert itm.exit_code == itm.EXIT_USAGE


def test_set_string():
    itm = tm.InteractiveTomcatManager()
    prompt = str(uuid.uuid1())
    itm.onecmd_plus_hooks("set prompt={}".format(prompt))
    assert itm.prompt == prompt
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_set_float_valid():
    itm = tm.InteractiveTomcatManager()
    itm.timeout = 10.0
    itm.onecmd_plus_hooks("set timeout=5.5")
    assert itm.timeout == 5.5
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_set_float_invalid():
    itm = tm.InteractiveTomcatManager()
    itm.debug = False
    itm.timeout = 10.0
    itm.onecmd_plus_hooks("set timeout=joe")
    assert itm.timeout == 10.0
    assert itm.exit_code == itm.EXIT_ERROR


def test_set_float_invalid_debug():
    itm = tm.InteractiveTomcatManager()
    itm.debug = True
    itm.timeout = 10.0
    itm.onecmd_plus_hooks("set timeout=joe")
    assert itm.timeout == 10.0
    assert itm.exit_code == itm.EXIT_ERROR


def test_set_boolean_valid():
    itm = tm.InteractiveTomcatManager()
    itm.echo = False
    itm.onecmd_plus_hooks("set echo=True")
    assert itm.echo is True
    assert itm.exit_code == itm.EXIT_SUCCESS


def test_set_boolean_invalid():
    itm = tm.InteractiveTomcatManager()
    itm.echo = False
    itm.onecmd_plus_hooks("set echo=notaboolean")
    assert itm.echo is False
    assert itm.exit_code == itm.EXIT_ERROR


def test_set_debug_invalid():
    itm = tm.InteractiveTomcatManager()
    itm.echo = False
    itm.debug = True
    itm.onecmd_plus_hooks("set echo=notaboolean")
    assert itm.echo is False
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
    itm.onecmd_plus_hooks("set timeout={}".format(timeout))
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert itm.timeout == timeout
    assert itm.tomcat.timeout == timeout


SETTINGS_SUCCESSFUL = [
    ("prompt=tm>", "tm>"),
    ("prompt=tm> ", "tm>"),
    ("prompt=t m>", "t m>"),
    ('prompt="tm> "', "tm> "),
    ('prompt="tm> "   # some comment here', "tm> "),
    ('prompt="t\'m> "', "t'm> "),
    ('prompt="""h\'i"""', "h'i"),
]


@pytest.mark.parametrize("arg, value", SETTINGS_SUCCESSFUL)
def test_do_set_success(arg, value):
    itm = tm.InteractiveTomcatManager()
    itm.do_set(arg)
    assert itm.prompt == value
    assert itm.exit_code == itm.EXIT_SUCCESS


SETTINGS_FAILURE = [
    "thisisntaparam=somevalue",
    "thisisntaparam",
]


@pytest.mark.parametrize("arg", SETTINGS_FAILURE)
def test_do_set_fail(arg):
    itm = tm.InteractiveTomcatManager()
    itm.do_set(arg)
    assert itm.exit_code == itm.EXIT_ERROR


PREFIXES = [
    ("--", "--"),
    ("*", "*"),
    (">>>", ">>>"),
    # with no prefix, we should see the connected message
    ("", "connected"),
]


@pytest.mark.parametrize("prefix, expected", PREFIXES)
def test_status_prefix(tomcat_manager_server, prefix, expected, capsys):
    itm = tm.InteractiveTomcatManager()
    itm.status_prefix = prefix
    itm.onecmd_plus_hooks(tomcat_manager_server.connect_command)
    out, err = capsys.readouterr()
    assert err.startswith(expected)
    assert itm.exit_code == itm.EXIT_SUCCESS


###
#
# test connect and which commands
#
###
def test_connect(tomcat_manager_server, capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks(tomcat_manager_server.connect_command)
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert_connected_to(itm, tomcat_manager_server.url, capsys)


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


@pytest.mark.parametrize("code, errmsg", FAIL_MESSAGES)
def test_connect_fail_ok(tomcat_manager_server, mocker, code, errmsg, capsys):
    itm = tm.InteractiveTomcatManager()
    itm.debug = False
    mock_ok = mocker.patch(
        "tomcatmanager.models.TomcatManagerResponse.response",
        new_callable=mock.PropertyMock,
    )
    qmr = MockResponse(code)
    mock_ok.return_value = qmr

    itm.onecmd_plus_hooks(tomcat_manager_server.connect_command)
    out, err = capsys.readouterr()
    assert not out
    assert errmsg in err
    assert itm.exit_code == itm.EXIT_ERROR


def test_connect_fail_not_found(tomcat_manager_server, mocker, capsys):
    itm = tm.InteractiveTomcatManager()
    itm.debug = False
    mock_ok = mocker.patch(
        "tomcatmanager.models.TomcatManagerResponse.response",
        new_callable=mock.PropertyMock,
    )
    qmr = MockResponse(requests.codes.not_found)
    mock_ok.return_value = qmr

    itm.onecmd_plus_hooks(tomcat_manager_server.connect_command)
    out, err = capsys.readouterr()
    assert not out
    assert "tomcat manager not found" in err
    assert itm.exit_code == itm.EXIT_ERROR


def test_connect_fail_other(tomcat_manager_server, mocker, capsys):
    itm = tm.InteractiveTomcatManager()
    itm.debug = False
    mock_ok = mocker.patch(
        "tomcatmanager.models.TomcatManagerResponse.response",
        new_callable=mock.PropertyMock,
    )
    qmr = MockResponse(requests.codes.server_error)
    mock_ok.return_value = qmr

    itm.onecmd_plus_hooks(tomcat_manager_server.connect_command)
    out, err = capsys.readouterr()
    assert not out
    assert "http error" in err
    assert itm.exit_code == itm.EXIT_ERROR


def test_connect_password_prompt(tomcat_manager_server, capsys, mocker):
    itm = tm.InteractiveTomcatManager()
    mock_getpass = mocker.patch("getpass.getpass")
    mock_getpass.return_value = tomcat_manager_server.password
    # this should call getpass.getpass, which is now mocked to return the password
    cmdline = "connect {} {}".format(
        tomcat_manager_server.url, tomcat_manager_server.user
    )
    itm.onecmd_plus_hooks(cmdline)
    # make sure it got called
    assert mock_getpass.call_count == 1
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert_connected_to(itm, tomcat_manager_server.url, capsys)


def test_connect_config(tomcat_manager_server, capsys, mocker):
    configname = str(uuid.uuid1())
    config = """[{}]
    url={}
    user={}
    password={}"""
    configstring = config.format(
        configname,
        tomcat_manager_server.url,
        tomcat_manager_server.user,
        tomcat_manager_server.password,
    )
    itm = itm_with_config(mocker, configstring)
    cmdline = "connect {}".format(configname)
    itm.onecmd_plus_hooks(cmdline)
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert_connected_to(itm, tomcat_manager_server.url, capsys)


def test_connect_config_user_override(tomcat_manager_server, mocker):
    configname = str(uuid.uuid1())
    config = """[{}]
    url={}
    user={}
    password={}"""
    configstring = config.format(
        configname,
        tomcat_manager_server.url,
        tomcat_manager_server.user,
        tomcat_manager_server.password,
    )
    itm = itm_with_config(mocker, configstring)
    cmdline = "connect {} someotheruser".format(configname)
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


def test_connect_config_user_password_override(tomcat_manager_server, mocker):
    configname = str(uuid.uuid1())
    config = """[{}]
    url={}
    user={}
    password={}"""
    configstring = config.format(
        configname,
        tomcat_manager_server.url,
        tomcat_manager_server.user,
        tomcat_manager_server.password,
    )
    itm = itm_with_config(mocker, configstring)
    cmdline = "connect {} someotheruser someotherpassword".format(configname)
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


def test_connect_config_cert(tomcat_manager_server, mocker):
    configname = str(uuid.uuid1())
    config = """[{}]
    url={}
    cert=/tmp/mycert"""
    configstring = config.format(
        configname,
        tomcat_manager_server.url,
    )
    itm = itm_with_config(mocker, configstring)
    cmdline = "connect {}".format(configname)
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


def test_connect_config_cert_override(tomcat_manager_server, mocker):
    configname = str(uuid.uuid1())
    config = """[{}]
    url={}
    cert=/tmp/mycert"""
    configstring = config.format(
        configname,
        tomcat_manager_server.url,
    )
    itm = itm_with_config(mocker, configstring)
    cmdline = "connect {} --cert /tmp/yourcert".format(configname)
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


def test_connect_config_cert_key(tomcat_manager_server, mocker):
    configname = str(uuid.uuid1())
    config = """[{}]
    url={}
    cert=/tmp/mycert
    key=/tmp/mykey"""
    configstring = config.format(
        configname,
        tomcat_manager_server.url,
    )
    itm = itm_with_config(mocker, configstring)
    cmdline = "connect {}".format(configname)
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


def test_connect_config_cert_key_override(tomcat_manager_server, mocker):
    configname = str(uuid.uuid1())
    config = """[{}]
    url={}
    cert=/tmp/mycert
    key=/tmp/mykey"""
    configstring = config.format(
        configname,
        tomcat_manager_server.url,
    )
    itm = itm_with_config(mocker, configstring)
    cmdline = "connect {} --cert /tmp/yourcert --key /tmp/yourkey".format(configname)
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


def test_connect_config_cacert(tomcat_manager_server, mocker):
    configname = str(uuid.uuid1())
    config = """[{}]
    url={}
    user={}
    password={}
    cacert=/tmp/cabundle"""
    configstring = config.format(
        configname,
        tomcat_manager_server.url,
        tomcat_manager_server.user,
        tomcat_manager_server.password,
    )
    itm = itm_with_config(mocker, configstring)
    cmdline = "connect {}".format(configname)
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


def test_connect_config_cacert_override(tomcat_manager_server, mocker):
    configname = str(uuid.uuid1())
    config = """[{}]
    url={}
    user={}
    password={}
    cacert=/tmp/cabundle"""
    configstring = config.format(
        configname,
        tomcat_manager_server.url,
        tomcat_manager_server.user,
        tomcat_manager_server.password,
    )
    itm = itm_with_config(mocker, configstring)
    cmdline = "connect {} --cacert /tmp/other".format(configname)
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


def test_connect_config_noverify_override(tomcat_manager_server, mocker):
    configname = str(uuid.uuid1())
    config = """[{}]
    url={}
    user={}
    password={}
    verify=True"""
    configstring = config.format(
        configname,
        tomcat_manager_server.url,
        tomcat_manager_server.user,
        tomcat_manager_server.password,
    )
    itm = itm_with_config(mocker, configstring)
    cmdline = "connect {} --noverify".format(configname)
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


def test_connect_config_noverify_override_cacert(tomcat_manager_server, mocker):
    configname = str(uuid.uuid1())
    config = """[{}]
    url={}
    user={}
    password={}
    cacert=/tmp/cabundle"""
    configstring = config.format(
        configname,
        tomcat_manager_server.url,
        tomcat_manager_server.user,
        tomcat_manager_server.password,
    )
    itm = itm_with_config(mocker, configstring)
    cmdline = "connect {} --noverify".format(configname)
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


def test_connect_config_password_prompt(tomcat_manager_server, capsys, mocker):
    configname = str(uuid.uuid1())
    config = """[{}]
    url={}
    user={}"""
    configstring = config.format(
        configname, tomcat_manager_server.url, tomcat_manager_server.user
    )
    itm = itm_with_config(mocker, configstring)
    mock_getpass = mocker.patch("getpass.getpass")
    mock_getpass.return_value = tomcat_manager_server.password
    # this will call getpass.getpass, which is now mocked to return the password
    cmdline = "connect {}".format(configname)
    itm.onecmd_plus_hooks(cmdline)
    assert mock_getpass.call_count == 1
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert_connected_to(itm, tomcat_manager_server.url, capsys)


def test_connect_with_connection_error(tomcat_manager_server, capsys, mocker):
    connect_mock = mocker.patch("tomcatmanager.TomcatManager.connect")
    connect_mock.side_effect = requests.exceptions.ConnectionError()
    itm = tm.InteractiveTomcatManager()
    itm.debug = False
    itm.onecmd_plus_hooks(tomcat_manager_server.connect_command)
    out, err = capsys.readouterr()
    assert not out
    assert connect_mock.call_count == 1
    assert err == "connection error\n"
    assert itm.exit_code == itm.EXIT_ERROR


def test_connect_with_connection_error_debug(tomcat_manager_server, capsys, mocker):
    connect_mock = mocker.patch("tomcatmanager.TomcatManager.connect")
    connect_mock.side_effect = requests.exceptions.ConnectionError()
    itm = tm.InteractiveTomcatManager()
    itm.debug = True
    itm.onecmd_plus_hooks(tomcat_manager_server.connect_command)
    out, err = capsys.readouterr()
    assert not out
    assert connect_mock.call_count == 1
    assert "requests.exceptions.ConnectionError" in err
    assert itm.exit_code == itm.EXIT_ERROR


def test_connect_with_timeout(tomcat_manager_server, capsys, mocker):
    connect_mock = mocker.patch("tomcatmanager.TomcatManager.connect")
    connect_mock.side_effect = requests.exceptions.Timeout()
    itm = tm.InteractiveTomcatManager()
    itm.debug = False
    itm.onecmd_plus_hooks(tomcat_manager_server.connect_command)
    out, err = capsys.readouterr()
    assert not out
    assert connect_mock.call_count == 1
    assert err == "connection timeout\n"
    assert itm.exit_code == itm.EXIT_ERROR


def test_connect_with_timeout_debug(tomcat_manager_server, capsys, mocker):
    connect_mock = mocker.patch("tomcatmanager.TomcatManager.connect")
    connect_mock.side_effect = requests.exceptions.Timeout()
    itm = tm.InteractiveTomcatManager()
    itm.debug = True
    itm.onecmd_plus_hooks(tomcat_manager_server.connect_command)
    out, err = capsys.readouterr()
    assert not out
    assert connect_mock.call_count == 1
    assert "requests.exceptions.Timeout" in err
    assert itm.exit_code == itm.EXIT_ERROR


def test_which(tomcat_manager_server, capsys):
    itm = get_itm(tomcat_manager_server)
    # force this to ensure `which` sets it to SUCCESS
    itm.exit_code = itm.EXIT_ERROR
    itm.onecmd_plus_hooks("which")
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert tomcat_manager_server.url in out
    assert tomcat_manager_server.user in out


def test_which_cert(tomcat_manager_server, capsys, mocker):
    # the mock tomcat erver can't authenticate using a certificate
    # so we connect as normal, then mock it so it appears
    # like we authenticated with a certificate
    itm = get_itm(tomcat_manager_server)
    cert_mock = mocker.patch(
        "tomcatmanager.TomcatManager.cert",
        new_callable=mock.PropertyMock,
    )
    cert_mock.return_value = "/tmp/mycert"
    itm.onecmd_plus_hooks("which")
    out, err = capsys.readouterr()
    assert "/tmp/mycert" in out


def test_which_cert_key(tomcat_manager_server, capsys, mocker):
    # the mock tomcat erver can't authenticate using a certificate
    # so we connect as normal, then mock it so it appears
    # like we authenticated with a certificate
    itm = get_itm(tomcat_manager_server)
    cert_mock = mocker.patch(
        "tomcatmanager.TomcatManager.cert",
        new_callable=mock.PropertyMock,
    )
    cert_mock.return_value = ("/tmp/mycert", "/tmp/mykey")
    itm.onecmd_plus_hooks("which")
    out, err = capsys.readouterr()
    assert "/tmp/mykey" in out


REQUIRES_CONNECTION = [
    "which",
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
]


@pytest.mark.parametrize("command", REQUIRES_CONNECTION)
def test_requires_connection(command, capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks(command)
    out, err = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_ERROR
    assert not out
    assert err == "not connected\n"


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
    itm.onecmd_plus_hooks("{} argument".format(cmdname))
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


def test_resources(tomcat_manager_server, capsys):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.EXIT_ERROR
    itm.onecmd_plus_hooks("resources")
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_SUCCESS
    assert "UserDatabase: " in out


def test_resources_class_name(tomcat_manager_server, capsys):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.EXIT_SUCCESS
    # this class has to be hand coded in the mock server
    itm.onecmd_plus_hooks("resources com.example.Nothing")
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.EXIT_ERROR
    assert not out


def test_findleakers(tomcat_manager_server):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.EXIT_ERROR
    itm.onecmd_plus_hooks("findleakers")
    assert itm.exit_code == itm.EXIT_SUCCESS


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
    assert out == "{}\n".format(itm.EXIT_SUCCESS)


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
    assert err == "unknown command: {}\n".format(cmdline)


def test_license(capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks("license")
    out, _ = capsys.readouterr()
    expected = """
Copyright 2007 Jared Crapo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
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
