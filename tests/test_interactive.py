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


###
#
# tests
#
###
def test__change_setting(itm):
    p = str(uuid.uuid1())
    # we know prompt is in itm.settable
    itm._change_setting('prompt', p)
    assert itm.prompt == p


def test__change_setting_with_invalid_param(itm):
    # this uuid won't be in itm.settable
    p = str(uuid.uuid1())
    with pytest.raises(ValueError):
        itm._change_setting(p, 'someval')


set_success = [
    ('prompt=tm>', 'tm>'),
    ('prompt=tm> ', 'tm>'),
    ('prompt=t m>', 't m>'),
    ('prompt="tm> "', 'tm> '),
    ('prompt="tm> "   # some comment here', 'tm> '),
    ('prompt="t\'m> "', "t\'m> "),
    ('prompt="""h\'i"""', "h'i"),
]
@pytest.mark.parametrize('arg, value', set_success)
def test_do_set_success(itm, arg, value):
    itm.do_set(arg)
    assert itm.prompt == value
    assert itm.exit_code == itm.exit_codes.success


set_fail = [
    'thisisntaparam=somevalue',
    'thisisntaparam',
]
@pytest.mark.parametrize('arg', set_fail)
def test_do_set_fail(itm, arg):
    itm.do_set(arg)
    assert itm.exit_code == itm.exit_codes.error


def test_do_set_with_no_args(itm):
    # this is supposed to be a success and show the usage information
    itm.do_set('')
    assert itm.exit_code == itm.exit_codes.success


booleans = [
    (    '1', True),
    (    '0', False),    
    (    'y', True),
    (    'Y', True),
    (  'yes', True),
    (  'Yes', True),
    (  'YES', True),
    (    'n', False),
    (    'N', False),
    (   'no', False),
    (   'No', False),
    (   'NO', False),
    (   'on', True),
    (   'On', True),
    (   'ON', True),
    (  'off', False),
    (  'Off', False),
    (  'OFF', False),
    ( 'true', True),
    ( 'True', True),
    ( 'TRUE', True),
    ('false', False),
    ('False', False),
    ('FALSE', False),
    (   True, True),
    (  False, False),
]
@pytest.mark.parametrize('str, value', booleans)
def test__convert_to_boolean(itm, str, value):
    assert itm.convert_to_boolean(str) == value


pythonizers = [
    ('fred', 'fred'),
    ('fred ', "'fred '"),
    ("can't ", '"can\'t "'),
    ('b"d', '\'b"d\''),
    ('b\'|"d', "\'b\\'|\"d'"),
]
@pytest.mark.parametrize('str, value', pythonizers)
def test_pythonize(itm, str, value):
    assert itm._pythonize(str) == value
