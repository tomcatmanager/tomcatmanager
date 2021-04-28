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
# pylint: disable=protected-access, missing-function-docstring
# pylint: disable=missing-module-docstring, unused-variable

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
    with open(localwar_file, "rb") as localwar_fileobj:
        assert tm.TomcatManager()._is_stream(localwar_fileobj)


def test_is_stream_bytesio():
    fileobj = io.BytesIO(b"the contents of my warfile")
    assert tm.TomcatManager()._is_stream(fileobj)


def test_is_stream_primitives():
    assert not tm.TomcatManager()._is_stream(None)
    assert not tm.TomcatManager()._is_stream("some string")
    assert not tm.TomcatManager()._is_stream(["some", "list"])


###
#
# connect
#
###
def test_connect_no_url():
    tomcat = tm.TomcatManager()
    assert not tomcat.is_connected
    with pytest.raises(requests.exceptions.MissingSchema):
        r = tomcat.connect("")


def test_connect_noauth(tomcat_manager_server):
    tomcat = tm.TomcatManager()
    assert not tomcat.is_connected
    r = tomcat.connect(tomcat_manager_server.url)
    assert isinstance(r, tm.models.TomcatManagerResponse)
    assert not tomcat.is_connected
    with pytest.raises(requests.exceptions.HTTPError):
        r.raise_for_status()


def test_connect_passwdauth(tomcat_manager_server):
    tomcat = tm.TomcatManager()
    assert not tomcat.is_connected
    assert not tomcat.tomcat_major_minor
    r = tomcat.connect(
        tomcat_manager_server.url,
        tomcat_manager_server.user,
        tomcat_manager_server.password,
        cert=tomcat_manager_server.cert,
    )
    assert isinstance(r, tm.models.TomcatManagerResponse)
    assert r.status_code == tm.StatusCode.OK
    assert r.server_info
    assert tomcat.is_connected
    assert tomcat.tomcat_major_minor
    assert tomcat.url
    r.raise_for_status()


def test_connect_certauth(tomcat_manager_server, mocker):
    get_mock = mocker.patch("requests.get")
    tomcat = tm.TomcatManager()
    assert not tomcat.is_connected
    assert not tomcat.tomcat_major_minor
    r = tomcat.connect(
        tomcat_manager_server.url,
        "",
        "",
        cert="/f1",
    )
    url = tomcat_manager_server.url + "/text/serverinfo"
    get_mock.assert_called_once_with(
        url,
        auth=None,
        params=None,
        timeout=tomcat.timeout,
        verify=True,
        cert="/f1",
    )


def test_connect_certkeyauth(tomcat_manager_server, mocker):
    get_mock = mocker.patch("requests.get")
    tomcat = tm.TomcatManager()
    assert not tomcat.is_connected
    assert not tomcat.tomcat_major_minor
    r = tomcat.connect(
        tomcat_manager_server.url,
        "",
        "",
        cert=("/f1", "/f2"),
    )
    url = tomcat_manager_server.url + "/text/serverinfo"
    get_mock.assert_called_once_with(
        url,
        auth=None,
        params=None,
        timeout=tomcat.timeout,
        verify=True,
        cert=("/f1", "/f2"),
    )


def test_connect_verifybundle(tomcat_manager_server, mocker):
    get_mock = mocker.patch("requests.get")
    tomcat = tm.TomcatManager()
    assert not tomcat.is_connected
    assert not tomcat.tomcat_major_minor
    r = tomcat.connect(
        tomcat_manager_server.url,
        "",
        "",
        verify="/tmp/cabundle",
    )
    url = tomcat_manager_server.url + "/text/serverinfo"
    get_mock.assert_called_once_with(
        url,
        auth=None,
        params=None,
        timeout=tomcat.timeout,
        verify="/tmp/cabundle",
        cert=None,
    )


def test_connect_noverify(tomcat_manager_server, mocker):
    get_mock = mocker.patch("requests.get")
    tomcat = tm.TomcatManager()
    assert not tomcat.is_connected
    assert not tomcat.tomcat_major_minor
    r = tomcat.connect(
        tomcat_manager_server.url,
        tomcat_manager_server.user,
        tomcat_manager_server.password,
        verify=False,
    )
    url = tomcat_manager_server.url + "/text/serverinfo"
    get_mock.assert_called_once_with(
        url,
        auth=(tomcat_manager_server.user, tomcat_manager_server.password),
        params=None,
        timeout=tomcat.timeout,
        verify=False,
        cert=None,
    )


def test_connect_connection_error(tomcat_manager_server, mocker):
    get_mock = mocker.patch("requests.get")
    get_mock.side_effect = requests.exceptions.ConnectionError()
    tomcat = tm.TomcatManager()
    assert not tomcat.is_connected
    assert not tomcat.tomcat_major_minor
    with pytest.raises(requests.exceptions.ConnectionError):
        r = tomcat.connect(
            tomcat_manager_server.url,
            tomcat_manager_server.user,
            tomcat_manager_server.password,
            cert=tomcat_manager_server.cert,
            verify=tomcat_manager_server.verify,
        )
    assert not tomcat.is_connected
    assert not tomcat.tomcat_major_minor
    assert not tomcat.url
    assert not tomcat.user
    assert not tomcat.cert
    assert not tomcat.verify


def test_connect_timeout(tomcat_manager_server, mocker):
    get_mock = mocker.patch("requests.get")
    get_mock.side_effect = requests.exceptions.Timeout()
    tomcat = tm.TomcatManager()
    assert not tomcat.is_connected
    assert not tomcat.tomcat_major_minor
    with pytest.raises(requests.exceptions.Timeout):
        r = tomcat.connect(
            tomcat_manager_server.url,
            tomcat_manager_server.user,
            tomcat_manager_server.password,
            cert=tomcat_manager_server.cert,
            verify=tomcat_manager_server.verify,
        )
    assert not tomcat.is_connected
    assert not tomcat.tomcat_major_minor
    assert not tomcat.url
    assert not tomcat.user
    assert not tomcat.cert
    assert not tomcat.verify


def test_connect_sets_timeout(tomcat_manager_server):
    tomcat = tm.TomcatManager()
    tomcat.timeout = 10
    assert not tomcat.is_connected
    assert not tomcat.tomcat_major_minor
    r = tomcat.connect(
        tomcat_manager_server.url,
        tomcat_manager_server.user,
        tomcat_manager_server.password,
        timeout=5,
    )
    assert isinstance(r, tm.models.TomcatManagerResponse)
    assert r.status_code == tm.StatusCode.OK
    assert r.server_info
    assert tomcat.is_connected
    assert tomcat.tomcat_major_minor
    assert tomcat.timeout == 5
    r.raise_for_status()
