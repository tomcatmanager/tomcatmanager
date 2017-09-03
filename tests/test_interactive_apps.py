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

import unittest.mock as mock

import pytest

import tomcatmanager as tm


def get_itm(tms):
    """
    Using this as a fixture with capsys breaks capsys. So we use a function.
    """
    itm = tm.InteractiveTomcatManager()
    args = 'connect {url} {user} {password}'.format(**tms)
    itm.onecmd_plus_hooks(args)
    return itm

def parse_apps(lines):
    apps = []
    for line in lines.splitlines():
        app = tm.models.TomcatApplication()
        app.parse(line)
        apps.append(app)
    return apps

###
#
# list
#
###
@pytest.fixture()
def mock_apps(mocker):
    return mocker.patch('tomcatmanager.models.TomcatManagerResponse.result', create=True,
                         new_callable=mock.PropertyMock)

def test_group_and_sort_empty():
    lines = ''
    itm = tm.InteractiveTomcatManager()
    args = itm.list_parse_args('')
    apps = parse_apps(lines)
    grouped_apps = itm.group_and_sort_apps(apps, args)
    assert isinstance(grouped_apps, list)
    assert len(grouped_apps) == 0
    
def test_group_and_sort_two_groups():
    lines = """/:running:0:ROOT
/shiny:stopped:17:shiny##v2.0.6
"""
    itm = tm.InteractiveTomcatManager()
    args = itm.list_parse_args('')
    apps = parse_apps(lines)
    grouped_apps = itm.group_and_sort_apps(apps, args)
    assert len(grouped_apps) == 2
    assert len(grouped_apps[0]) == 1
    assert len(grouped_apps[1]) == 1

def test_list_parse_args_raw():
    argv = '--raw'
    itm = tm.InteractiveTomcatManager()
    args = itm.list_parse_args(argv)
    assert args.raw == True
    
def test_list_raw(tomcat_manager_server, mock_apps, capsys):
    lines = """/:running:0:ROOT
/shiny:stopped:17:shiny##v2.0.6
/shiny:running:15:shiny##v2.0.7
/host-manager:running:0:/usr/share/tomcat8-admin/host-manager
/manager:running:0:/usr/share/tomcat8-admin/manager
""" 
    mock_apps.return_value = lines
    interactive_tomcat = get_itm(tomcat_manager_server)
    interactive_tomcat.onecmd_plus_hooks('list --raw')
    out, err = capsys.readouterr()
    assert out == lines
