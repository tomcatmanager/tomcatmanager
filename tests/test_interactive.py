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
@pytest.fixture()
def itm():
    return tm.InteractiveTomcatManager()

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
def test_load_config(itm, mocker):
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

    
def test__change_setting(itm):
    prompt = str(uuid.uuid1())
    # we know prompt is in itm.settable
    itm._change_setting('prompt', prompt)
    assert itm.prompt == prompt

def test__change_setting_with_invalid_param(itm):
    # this uuid won't be in itm.settable
    invalid_setting = str(uuid.uuid1())
    with pytest.raises(ValueError):
        itm._change_setting(invalid_setting, 'someval')

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
def test_do_set_success(itm, arg, value):
    itm.do_set(arg)
    assert itm.prompt == value
    assert itm.exit_code == itm.exit_codes.success

SETTINGS_FAILURE = [
    'thisisntaparam=somevalue',
    'thisisntaparam',
]
@pytest.mark.parametrize('arg', SETTINGS_FAILURE)
def test_do_set_fail(itm, arg):
    itm.do_set(arg)
    assert itm.exit_code == itm.exit_codes.error

def test_do_set_with_no_args(itm):
    # this is supposed to be a success and show the usage information
    itm.do_set('')
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
def test__convert_to_boolean(itm, param, value):
    assert itm.convert_to_boolean(param) == value


LITERALS = [
    ('fred', 'fred'),
    ('fred ', "'fred '"),
    ("can't ", '"can\'t "'),
    ('b"d', '\'b"d\''),
    ('b\'|"d', "\'b\\'|\"d'"),
]
@pytest.mark.parametrize('param, value', LITERALS)
def test_pythonize(itm, param, value):
    assert itm._pythonize(param) == value
