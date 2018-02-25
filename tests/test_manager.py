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

import io

import pytest
import requests

import tomcatmanager as tm

###
#
# is_stream
#
###
def test_is_stream_fileobj(localwar_file):
    with open(localwar_file, 'rb') as localwar_fileobj:
        assert tm.TomcatManager()._is_stream(localwar_fileobj)

def test_is_stream_bytesio():
    fileobj = io.BytesIO(b'the contents of my warfile')
    assert tm.TomcatManager()._is_stream(fileobj)

def test_is_stream_primitives():
    assert not tm.TomcatManager()._is_stream(None)
    assert not tm.TomcatManager()._is_stream('some string')
    assert not tm.TomcatManager()._is_stream(['some', 'list'])


###
#
# connect
#
###
def test_connect_no_url():
    tomcat = tm.TomcatManager()
    with pytest.raises(requests.exceptions.MissingSchema):
        r = tomcat.connect('')

def test_connect_noauth(tomcat_manager_server):
    tomcat = tm.TomcatManager()
    r = tomcat.connect(tomcat_manager_server.url)
    assert isinstance(r, tm.models.TomcatManagerResponse)
    assert not tomcat.is_connected
    with pytest.raises(requests.exceptions.HTTPError):
        r.raise_for_status()

def test_connect_auth(tomcat_manager_server):
    tomcat = tm.TomcatManager()
    r = tomcat.connect(
        tomcat_manager_server.url,
        tomcat_manager_server.user,
        tomcat_manager_server.password
    )
    assert isinstance(r, tm.models.TomcatManagerResponse)
    assert r.status_code == tm.status_codes.ok
    assert tomcat.is_connected
    assert r.result == ''
    assert r.status_message == ''
    r.raise_for_status()

def test_connect_connection_error(tomcat_manager_server, mocker):
    get_mock = mocker.patch('requests.get')
    get_mock.side_effect = requests.exceptions.ConnectionError()
    tomcat = tm.TomcatManager()
    with pytest.raises(requests.exceptions.ConnectionError):
        r = tomcat.connect(
            tomcat_manager_server.url,
            tomcat_manager_server.user,
            tomcat_manager_server.password
        )

def test_connect_timeout(tomcat_manager_server, mocker):
    get_mock = mocker.patch('requests.get')
    get_mock.side_effect = requests.exceptions.Timeout()
    tomcat = tm.TomcatManager()
    with pytest.raises(requests.exceptions.Timeout):
        r = tomcat.connect(
            tomcat_manager_server.url,
            tomcat_manager_server.user,
            tomcat_manager_server.password
        )
