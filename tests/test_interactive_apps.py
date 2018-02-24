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


###
#
# list
#
###
@pytest.fixture()
def mock_apps(mocker):
    return mocker.patch('tomcatmanager.models.TomcatManagerResponse.result', create=True,
                        new_callable=mock.PropertyMock)

def parse_apps(lines):
    """helper function to turn colon seperated text into objects"""
    apps = []
    for line in lines.splitlines():
        app = tm.models.TomcatApplication()
        app.parse(line)
        apps.append(app)
    return apps

def test_list_process_apps_empty():
    lines = ''
    itm = tm.InteractiveTomcatManager()
    args = itm.parse_args(itm.list_parser, '')
    apps = parse_apps(lines)
    apps = itm._list_process_apps(apps, args)
    assert isinstance(apps, list)
    assert apps == []

LIST_ARGV_BAD = [
    '-raw',
    '--raw -b tate',
    '--by=version',
    '-s loading',
    '-sl',
    '-bs',
]
@pytest.mark.parametrize('argv', LIST_ARGV_BAD)
def test_list_parse_args_failure(argv):
    itm = tm.InteractiveTomcatManager()
    with pytest.raises(SystemExit):
        itm.parse_args(itm.list_parser, argv)
    assert itm.exit_code == itm.exit_codes.usage

@pytest.mark.parametrize('raw', ['', '-r', '--raw'])
@pytest.mark.parametrize(
    'state',
    ['', '-s running', '-s stopped', '--state=running', '--state=stopped'],
)
@pytest.mark.parametrize(
    'sort',
    ['', '-b state', '-b path', '--by=state', '--by=path'],
)
def test_list_parse_args(raw, state, sort):
    itm = tm.InteractiveTomcatManager()
    argv = '{} {} {}'.format(raw, state, sort)
    itm.parse_args(itm.list_parser, argv)
    assert itm.exit_code == itm.exit_codes.success

def test_list_sort_by_state(tomcat_manager_server, mock_apps, capsys):
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
    mock_apps.return_value = raw_apps
    interactive_tomcat = get_itm(tomcat_manager_server)
    interactive_tomcat.onecmd_plus_hooks('list --raw -b state')
    out, _ = capsys.readouterr()
    assert out == expected

def test_list_sort_by_path(tomcat_manager_server, mock_apps, capsys):
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
    mock_apps.return_value = raw_apps
    interactive_tomcat = get_itm(tomcat_manager_server)
    interactive_tomcat.onecmd_plus_hooks('list --raw -b path')
    out, _ = capsys.readouterr()
    assert out == expected

def test_list_state_running(tomcat_manager_server, mock_apps, capsys):
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
    mock_apps.return_value = raw_apps
    interactive_tomcat = get_itm(tomcat_manager_server)
    interactive_tomcat.onecmd_plus_hooks('list --raw -s running')
    out, _ = capsys.readouterr()
    assert out == expected
