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
# fixtures
#
###
def fake_load_config(self):
    self.config = None

@pytest.fixture()
def itm_nc(mocker):
    """Don't allow it to load a config file"""
    mocker.patch('tomcatmanager.InteractiveTomcatManager.load_config')
    itm = tm.InteractiveTomcatManager()
    return itm

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
    itm = tm.InteractiveTomcatManager()
    prompt = str(uuid.uuid1())
    fd, fname = tempfile.mkstemp(prefix='', suffix='.ini')
    os.close(fd)
    with open(fname, 'w') as fobj:
        fobj.write('[settings]\nprompt={}\n'.format(prompt))

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
        # now make sure that our file got loaded properly
        assert itm.prompt == prompt
    finally:
        os.remove(fname)

def test_set_string():
    itm = tm.InteractiveTomcatManager()
    prompt = str(uuid.uuid1())
    command = 'set prompt={}'.format(prompt)
    itm.onecmd_plus_hooks(command)
    assert itm.prompt == prompt
    assert itm.exit_code == itm.exit_codes.success

def test_set_noargs(capsys):
    itm = tm.InteractiveTomcatManager()
    itm.onecmd_plus_hooks('set')
    out, err = capsys.readouterr()
    assert out == 'hi'
    assert itm.exit_code == itm.exit_codes.success

def test_set_integer_valid():
    itm = tm.InteractiveTomcatManager()
    itm.timeout = 10
    itm.onecmd_plus_hooks('set timeout=5')
    assert itm.timeout == 5
    assert itm.exit_code == itm.exit_codes.success

def test_set_integer_invalid(capsys):
    itm = tm.InteractiveTomcatManager()
    itm.timeout = 10
    itm.onecmd_plus_hooks('set timeout=joe')
    assert itm.timeout == 10
    assert itm.exit_code == itm.exit_codes.error

def test_set_boolean_valid():
    itm = tm.InteractiveTomcatManager()
    itm.echo = False
    itm.onecmd_plus_hooks('set echo=True')
    assert itm.echo == True
    assert itm.exit_code == itm.exit_codes.success

def test_set_boolean_invalid():
    itm = tm.InteractiveTomcatManager()
    itm.echo = False
    itm.onecmd_plus_hooks('set echo=notaboolean')
    assert itm.echo == False
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
@pytest.mark.parametrize('param', BOOLEANS)
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
