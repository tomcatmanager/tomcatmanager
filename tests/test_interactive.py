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

import uuid
import unittest.mock as mock
import tempfile
import os

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

@pytest.fixture()
def itm_nc(mocker):
    """Don't allow it to load a config file"""
    mocker.patch('tomcatmanager.InteractiveTomcatManager.load_config')
    itm = tm.InteractiveTomcatManager()
    return itm

###
#
# test help command line options
#
###
HELP_COMMANDS = [
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
]
@pytest.mark.parametrize('command', HELP_COMMANDS)
def test_command_help(tomcat_manager_server, command):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.exit_codes.error
    itm.onecmd_plus_hooks('{} -h'.format(command))
    assert itm.exit_code == itm.exit_codes.usage

    itm.exit_code = itm.exit_codes.error
    itm.onecmd_plus_hooks('{} --help'.format(command))
    assert itm.exit_code == itm.exit_codes.usage

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

def test_which(tomcat_manager_server, capsys):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.exit_codes.error
    itm.onecmd_plus_hooks('which')
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.exit_codes.success
    assert tomcat_manager_server['url'] in out


###
#
# test config and settings commands
#
###
def test_do_edit(itm_nc, mocker):
    itm_nc.editor = 'fooedit'
    mock_os_system = mocker.patch('os.system')
    itm_nc.onecmd('config edit')
    assert mock_os_system.call_count == 1


###
#
# test config and settings other methods
#
###
def test_load_config(mocker):
    prompt = str(uuid.uuid1())
    configstring = '[settings]\nprompt={}\n'.format(prompt)
    itm = itm_with_config(mocker, configstring)
    assert itm.prompt == prompt

def test_settings_noargs(capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks('settings')
    out, err = capsys.readouterr()
    # not going to parse all the lines, but there
    # should be one per setting
    assert len(out.splitlines()) == len(itm.settable)
    assert itm.exit_code == itm.exit_codes.success

def test_set_string():
    itm = tm.InteractiveTomcatManager()
    prompt = str(uuid.uuid1())
    command = 'set prompt={}'.format(prompt)
    itm.onecmd_plus_hooks(command)
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

def test__change_setting_hook():
    # make sure the hook gets called
    pass

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
    itm.onecmd('resources com.example.Nothing')
    out, _ = capsys.readouterr()
    assert itm.exit_code == itm.exit_codes.error
    assert not out

def test_findleakers(tomcat_manager_server):
    itm = get_itm(tomcat_manager_server)
    itm.exit_code = itm.exit_codes.error
    itm.onecmd_plus_hooks('findleakers')
    assert itm.exit_code == itm.exit_codes.success
