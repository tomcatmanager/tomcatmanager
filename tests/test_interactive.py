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

import os
import tempfile
import unittest.mock as mock
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
    args = 'connect {url} {user} {password}'.format(**tms)
    itm.onecmd_plus_hooks(args)
    return itm

def itm_with_config(mocker, configstring):
    """Return an InteractiveTomcatManager object with the config set from the passed string."""
    itm = tm.InteractiveTomcatManager()
    fd, fname = tempfile.mkstemp(prefix='', suffix='.ini')
    os.close(fd)
    with open(fname, 'w') as fobj:
        fobj.write(configstring)

    # itm aleady tried to load a config file, which it may or may not
    # have found, depending on if you have one or not
    # we are now going to patch up the config_file to point to
    # a known file, and the reload the config from that
    try:
        config_file = mocker.patch('tomcatmanager.InteractiveTomcatManager.config_file',
                                   new_callable=mock.PropertyMock)
        config_file.return_value = fname
        itm.load_config()
        # this just verifies that our patch worked
        assert itm.config_file == fname
    finally:
        os.remove(fname)
    return itm

def assert_connected_to(itm, url, capsys):
    itm.onecmd_plus_hooks('which')
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.exit_codes.success
    assert url in out

@pytest.fixture
def itm_nc(mocker):
    """Don't allow it to load a config file"""
    mocker.patch('tomcatmanager.InteractiveTomcatManager.load_config')
    itm = tm.InteractiveTomcatManager()
    return itm

###
#
# test help
#
###
HELP_COMMANDS = [
    'config',
    'show',
    'settings',
    'connect',
    'which',
    'deploy',
    'redeploy',
    'undeploy',
    'start',
    'stop',
    'reload',
    'restart',
    'sessions',
    'expire',
    'list',
    'serverinfo',
    'status',
    'vminfo',
    'sslconnectorciphers',
    'threaddump',
    'resources',
    'findleakers',
    'version',
    'license',
]
# exit_code omitted because it doesn't respond
# to -h or --help
@pytest.mark.parametrize('command', HELP_COMMANDS)
def test_command_help(tomcat_manager_server, command):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.exit_codes.error
    itm.onecmd_plus_hooks('{} -h'.format(command))
    assert itm.exit_code == itm.exit_codes.usage

    itm.exit_code = itm.exit_codes.error
    itm.onecmd_plus_hooks('{} --help'.format(command))
    assert itm.exit_code == itm.exit_codes.usage

# copy the list
HELP_ARGPARSERS = list(HELP_COMMANDS)
# there is an argparser for exit_code, but it's only used
# to generate the help
HELP_ARGPARSERS.append('exit_code')
@pytest.mark.parametrize('command', HELP_ARGPARSERS)
def test_help_matches_argparser(command, capsys):
    itm = tm.InteractiveTomcatManager()
    cmdline = 'help {}'.format(command)
    itm.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    parser_func = getattr(itm, '{}_parser'.format(command))
    assert out == parser_func.format_help()
    assert itm.exit_code == itm.exit_codes.success

def test_help_set(capsys):
    itm = tm.InteractiveTomcatManager()
    cmdline = 'help set'
    itm.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert 'change the value of one of this program\'s settings' in out
    assert itm.exit_code == itm.exit_codes.success

def test_help(capsys):
    itm = tm.InteractiveTomcatManager()
    cmdline = 'help'
    itm.onecmd_plus_hooks(cmdline)
    out, _ = capsys.readouterr()
    assert 'Connecting to a Tomcat server' in out
    assert 'Managing applications' in out
    assert 'Server information' in out
    assert 'Settings, configuration, and tools' in out
    assert itm.exit_code == itm.exit_codes.success


###
#
# test config and settings
#
###
BOOLEANS = [
    ('1', True),
    ('0', False),
    ('y', True),
    ('Y', True),
    ('yes', True),
    ('Yes', True),
    ('YES', True),
    ('n', False),
    ('N', False),
    ('no', False),
    ('No', False),
    ('NO', False),
    ('on', True),
    ('On', True),
    ('ON', True),
    ('off', False),
    ('Off', False),
    ('OFF', False),
    ('t', True),
    ('true', True),
    ('True', True),
    ('TRUE', True),
    ('f', False),
    ('false', False),
    ('False', False),
    ('FALSE', False),
    (True, True),
    (False, False),
]
@pytest.mark.parametrize('param, value', BOOLEANS)
def test_convert_to_boolean_valid(param, value):
    itm = tm.InteractiveTomcatManager()
    assert itm.convert_to_boolean(param) == value

NOT_BOOLEANS = [
    None,
    '',
    10,
    'ace',
]
@pytest.mark.parametrize('param', NOT_BOOLEANS)
def test_convert_to_boolean_invalid(param):
    itm = tm.InteractiveTomcatManager()
    with pytest.raises(ValueError):
        itm.convert_to_boolean(param)

LITERALS = [
    ('fred', 'fred'),
    ('fred ', "'fred '"),
    ("can't ", '"can\'t "'),
    ('b"d', '\'b"d\''),
    ('b\'|"d', "\'b\\'|\"d'"),
]
@pytest.mark.parametrize('param, value', LITERALS)
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
    itm_nc.editor = 'fooedit'
    mock_os_system = mocker.patch('os.system')
    itm_nc.onecmd_plus_hooks('config edit')
    assert mock_os_system.call_count == 1
    assert itm_nc.exit_code == itm_nc.exit_codes.success

def test_config_edit_no_editor(itm_nc, capsys):
    itm_nc.editor = None
    itm_nc.onecmd_plus_hooks('config edit')
    out, err = capsys.readouterr()
    assert itm_nc.exit_code == itm_nc.exit_codes.error
    assert not out
    assert err.startswith('no editor: ')

def test_config_invalid_action(itm_nc, capsys):
    itm_nc.onecmd_plus_hooks('config bogus')
    out, err = capsys.readouterr()
    assert itm_nc.exit_code == itm_nc.exit_codes.usage
    assert not out
    assert err.startswith('usage: ')

def test_config_file_command(mocker, capsys):
    fname = '/tmp/someconfig.ini'
    itm = tm.InteractiveTomcatManager()

    config_file = mocker.patch('tomcatmanager.InteractiveTomcatManager.config_file',
                               new_callable=mock.PropertyMock)
    config_file.return_value = fname

    itm.onecmd_plus_hooks('config file')
    out, _ = capsys.readouterr()
    assert out == '{}\n'.format(fname)
    assert itm.exit_code == itm.exit_codes.success

def test_load_config(mocker):
    prompt = str(uuid.uuid1())
    configstring = '[settings]\nprompt={}\n'.format(prompt)
    itm = itm_with_config(mocker, configstring)
    assert itm.prompt == prompt

def test_load_config_bogus_setting(mocker):
    configstring = '[settings]\nbogus=True\n'
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
    configstring = '[settings]\ntimeout=noganinteger\n'
    # this shouldn't throw any exceptions
    itm = itm_with_config(mocker, configstring)
    # make sure the timeout setting is the same
    # as when we don't load a config file
    assert itm_nc.timeout == itm.timeout

SHOW_SETTINGS = ['settings', 'show']
@pytest.mark.parametrize('command', SHOW_SETTINGS)
def test_show_noargs(command, capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks(command)
    out, _ = capsys.readouterr()
    # not going to parse all the lines, but there
    # should be one per setting
    assert len(out.splitlines()) == len(itm.settable)
    assert itm.exit_code == itm.exit_codes.success

@pytest.mark.parametrize('command', SHOW_SETTINGS)
def test_show_valid_setting(command, capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks('{} prompt'.format(command))
    out, _ = capsys.readouterr()
    assert out.startswith("prompt='{}' ".format(itm.prompt))
    assert itm.exit_code == itm.exit_codes.success

@pytest.mark.parametrize('command', SHOW_SETTINGS)
def test_show_invalid_setting(command, capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks('{} bogus'.format(command))
    out, err = capsys.readouterr()
    assert not out
    assert err == "unknown setting: 'bogus'\n"
    assert itm.exit_code == itm.exit_codes.error

def test_set_noargs(capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks('set')
    out, err = capsys.readouterr()
    assert not out
    assert err == 'invalid syntax: try {setting}={value}\n'
    assert itm.exit_code == itm.exit_codes.usage

def test_set_string():
    itm = tm.InteractiveTomcatManager()
    prompt = str(uuid.uuid1())
    itm.onecmd_plus_hooks('set prompt={}'.format(prompt))
    assert itm.prompt == prompt
    assert itm.exit_code == itm.exit_codes.success

def test_set_integer_valid():
    itm = tm.InteractiveTomcatManager()
    itm.timeout = 10
    itm.onecmd_plus_hooks('set timeout=5')
    assert itm.timeout == 5
    assert itm.exit_code == itm.exit_codes.success

def test_set_integer_invalid():
    itm = tm.InteractiveTomcatManager()
    itm.timeout = 10
    itm.onecmd_plus_hooks('set timeout=joe')
    assert itm.timeout == 10
    assert itm.exit_code == itm.exit_codes.error

def test_set_boolean_valid():
    itm = tm.InteractiveTomcatManager()
    itm.echo = False
    itm.onecmd_plus_hooks('set echo=True')
    assert itm.echo is True
    assert itm.exit_code == itm.exit_codes.success

def test_set_boolean_invalid():
    itm = tm.InteractiveTomcatManager()
    itm.echo = False
    itm.onecmd_plus_hooks('set echo=notaboolean')
    assert itm.echo is False
    assert itm.exit_code == itm.exit_codes.error

def test_set_with_invalid_param():
    itm = tm.InteractiveTomcatManager()
    # this uuid won't be in itm.settable
    invalid_setting = str(uuid.uuid1())
    with pytest.raises(ValueError):
        # pylint: disable=protected-access
        itm._change_setting(invalid_setting, 'someval')

def test_onchange_timout(mocker):
    timeout = 10
    hook = mocker.patch('tomcatmanager.InteractiveTomcatManager._onchange_timeout')
    itm = tm.InteractiveTomcatManager()
    # set this to a value that we know will cause it to change when we execute
    # the command
    itm.timeout = 5
    itm.onecmd_plus_hooks('set timeout={}'.format(timeout))
    assert itm.exit_code == itm.exit_codes.success
    assert hook.call_count == 1
    assert itm.tomcat.timeout == timeout

SETTINGS_SUCCESSFUL = [
    ('prompt=tm>', 'tm>'),
    ('prompt=tm> ', 'tm>'),
    ('prompt=t m>', 't m>'),
    ('prompt="tm> "', 'tm> '),
    ('prompt="tm> "   # some comment here', 'tm> '),
    ('prompt="t\'m> "', "t\'m> "),
    ('prompt="""h\'i"""', "h'i"),
]
@pytest.mark.parametrize('arg, value', SETTINGS_SUCCESSFUL)
def test_do_set_success(arg, value):
    itm = tm.InteractiveTomcatManager()
    itm.do_set(arg)
    assert itm.prompt == value
    assert itm.exit_code == itm.exit_codes.success

SETTINGS_FAILURE = [
    'thisisntaparam=somevalue',
    'thisisntaparam',
]
@pytest.mark.parametrize('arg', SETTINGS_FAILURE)
def test_do_set_fail(arg):
    itm = tm.InteractiveTomcatManager()
    itm.do_set(arg)
    assert itm.exit_code == itm.exit_codes.error

PREFIXES = [
    ('--', '--'),
    ('*', '*'),
    ('>>>', '>>>'),
    # with no prefix, we should see the connected message
    ('', 'connected'),
]
@pytest.mark.parametrize('prefix, expected', PREFIXES)
def test_status_prefix(tomcat_manager_server, prefix, expected, capsys):
    itm = tm.InteractiveTomcatManager()
    args = 'connect {url} {user} {password}'.format(**tomcat_manager_server)
    itm.status_prefix = prefix
    itm.onecmd_plus_hooks(args)
    out, err = capsys.readouterr()
    assert err.startswith(expected)
    assert itm.exit_code == itm.exit_codes.success

###
#
# test connect and which commands
#
###
def test_connect(tomcat_manager_server, capsys):
    itm = tm.InteractiveTomcatManager()
    cmdline = 'connect {url} {user} {password}'.format(**tomcat_manager_server)
    itm.onecmd_plus_hooks(cmdline)
    assert itm.exit_code == itm.exit_codes.success
    assert_connected_to(itm, tomcat_manager_server['url'], capsys)

def test_connect_password_prompt(tomcat_manager_server, capsys, mocker):
    itm = tm.InteractiveTomcatManager()
    mock_getpass = mocker.patch('getpass.getpass')
    mock_getpass.return_value = tomcat_manager_server['password']
    # this should call getpass.getpass, which is now mocked to return the password
    cmdline = 'connect {url} {user}'.format(**tomcat_manager_server)
    itm.onecmd_plus_hooks(cmdline)
    # make sure it got called
    assert mock_getpass.call_count == 1
    assert itm.exit_code == itm.exit_codes.success
    assert_connected_to(itm, tomcat_manager_server['url'], capsys)

def test_connect_config(tomcat_manager_server, capsys, mocker):
    configname = str(uuid.uuid1())
    config = """[{}]
    url={url}
    user={user}
    password={password}"""
    configstring = config.format(configname, **tomcat_manager_server)
    itm = itm_with_config(mocker, configstring)
    cmdline = 'connect {}'.format(configname)
    itm.onecmd_plus_hooks(cmdline)
    assert itm.exit_code == itm.exit_codes.success
    assert_connected_to(itm, tomcat_manager_server['url'], capsys)

def test_connect_config_password_prompt(tomcat_manager_server, capsys, mocker):
    configname = str(uuid.uuid1())
    config = """[{}]
    url={url}
    user={user}"""
    configstring = config.format(configname, **tomcat_manager_server)
    itm = itm_with_config(mocker, configstring)
    mock_getpass = mocker.patch('getpass.getpass')
    mock_getpass.return_value = tomcat_manager_server['password']
    # this will call getpass.getpass, which is now mocked to return the password
    cmdline = 'connect {}'.format(configname)
    itm.onecmd_plus_hooks(cmdline)
    assert mock_getpass.call_count == 1
    assert itm.exit_code == itm.exit_codes.success
    assert_connected_to(itm, tomcat_manager_server['url'], capsys)

def test_connect_with_connection_error(tomcat_manager_server, capsys, mocker):
    connect_mock = mocker.patch('tomcatmanager.TomcatManager.connect')
    connect_mock.side_effect = requests.exceptions.ConnectionError()
    itm = tm.InteractiveTomcatManager()
    cmdline = 'connect {url} {user} {password}'.format(**tomcat_manager_server)
    itm.onecmd_plus_hooks(cmdline)
    out, err = capsys.readouterr()
    assert not out
    assert connect_mock.call_count == 1
    assert err == 'connection error\n'
    assert itm.exit_code == itm.exit_codes.error

def test_connect_with_timeout(tomcat_manager_server, capsys, mocker):
    connect_mock = mocker.patch('tomcatmanager.TomcatManager.connect')
    connect_mock.side_effect = requests.exceptions.Timeout()
    itm = tm.InteractiveTomcatManager()
    cmdline = 'connect {url} {user} {password}'.format(**tomcat_manager_server)
    itm.onecmd_plus_hooks(cmdline)
    out, err = capsys.readouterr()
    assert not out
    assert connect_mock.call_count == 1
    assert err == 'connection timeout\n'
    assert itm.exit_code == itm.exit_codes.error

def test_which(tomcat_manager_server, capsys):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.exit_codes.error
    itm.onecmd_plus_hooks('which')
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.exit_codes.success
    assert tomcat_manager_server['url'] in out

REQUIRES_CONNECTION = [
    'which',
    'deploy',
    'redeploy',
    'undeploy',
    'start',
    'stop',
    'reload',
    'restart',
    'sessions',
    'expire',
    'list',
    'serverinfo',
    'status',
    'vminfo',
    'sslconnectorciphers',
    'threaddump',
    'resources',
    'findleakers',
]
@pytest.mark.parametrize('command', REQUIRES_CONNECTION)
def test_requires_connection(command, capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks(command)
    out, err = capsys.readouterr()
    assert itm.exit_code == itm.exit_codes.error
    assert not out
    assert err == 'not connected\n'


###
#
# test informational commands
#
###
NOARGS_INFO_COMMANDS = [
    'serverinfo',
    'status',
    'vminfo',
    'sslconnectorciphers',
    'threaddump',
    'findleakers',
]
@pytest.mark.parametrize('cmdname', NOARGS_INFO_COMMANDS)
def test_info_commands_noargs(tomcat_manager_server, cmdname):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.exit_codes.success
    itm.onecmd_plus_hooks('{} argument'.format(cmdname))
    assert itm.exit_code == itm.exit_codes.usage

def test_serverinfo(tomcat_manager_server, capsys):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.exit_codes.error
    itm.onecmd_plus_hooks('serverinfo')
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.exit_codes.success
    assert 'Tomcat Version: ' in out
    assert 'JVM Version: ' in out

def test_status(tomcat_manager_server, capsys):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.exit_codes.error
    itm.onecmd_plus_hooks('status')
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.exit_codes.success
    assert '</status>' in out
    assert '</jvm>' in out
    assert '</connector>' in out

def test_vminfo(tomcat_manager_server, capsys):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.exit_codes.error
    itm.onecmd_plus_hooks('vminfo')
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.exit_codes.success
    assert 'Runtime information:' in out
    assert 'architecture:' in out
    assert 'System properties:' in out

def test_sslconnectorciphers(tomcat_manager_server, capsys):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.exit_codes.error
    itm.onecmd_plus_hooks('sslconnectorciphers')
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.exit_codes.success
    assert 'Connector' in out
    assert 'SSL' in out

def test_threaddump(tomcat_manager_server, capsys):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.exit_codes.error
    itm.onecmd_plus_hooks('threaddump')
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.exit_codes.success
    assert 'java.lang.Thread.State' in out

def test_resources(tomcat_manager_server, capsys):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.exit_codes.error
    itm.onecmd_plus_hooks('resources')
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.exit_codes.success
    assert 'UserDatabase: ' in out

def test_resources_class_name(tomcat_manager_server, capsys):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.exit_codes.success
    # this class has to be hand coded in the mock server
    itm.onecmd_plus_hooks('resources com.example.Nothing')
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.exit_codes.error
    assert not out

def test_findleakers(tomcat_manager_server):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.exit_codes.error
    itm.onecmd_plus_hooks('findleakers')
    assert itm.exit_code == itm.exit_codes.success

###
#
# miscellaneous commands
#
###
def test_exit():
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks('exit')
    assert itm.exit_code == itm.exit_codes.success

def test_quit():
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks('quit')
    assert itm.exit_code == itm.exit_codes.success

def test_exit_code(capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks('version')
    out, _ = capsys.readouterr()
    itm.onecmd_plus_hooks('exit_code')
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.exit_codes.success
    assert out == '{}\n'.format(itm.exit_codes.success)

def test_version(capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks('version')
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.exit_codes.success
    assert tm.__version__ in out

def test_default(capsys):
    cmdline = 'notacommand'
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks(cmdline)
    out, err = capsys.readouterr()
    assert itm.exit_code == itm.exit_codes.command_not_found
    assert not out
    assert err == 'unknown command: {}\n'.format(cmdline)

def test_license(capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks('license')
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
