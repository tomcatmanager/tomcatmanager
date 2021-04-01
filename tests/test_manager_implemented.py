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

import unittest.mock as mock

import pytest
import requests

import tomcatmanager as tm


def test_implemented_by_invalid(mocker):
    # - this test makes sure the _implemented_by decorator throws the proper exceptions
    # - it depends on ssl_reload() being decorated as not implemented in TomcatMajor.V7
    # - this does not attempt to test whether various methods are decorated with the
    #   proper versions of Tomcat
    tomcat = tm.TomcatManager()
    with pytest.raises(tm.TomcatNotConnected):
        response = tomcat.ssl_reload()
    # pretend we are connected and use an invalid version
    cmock = mocker.patch(
        "tomcatmanager.tomcat_manager.TomcatManager.is_connected",
        new_callable=mock.PropertyMock,
    )
    cmock.return_value = True
    vmock = mocker.patch(
        "tomcatmanager.tomcat_manager.TomcatManager.tomcat_major",
        new_callable=mock.PropertyMock,
    )
    vmock.return_value = tm.TomcatMajor.V7

    with pytest.raises(tm.TomcatNotImplementedError):
        response = tomcat.ssl_reload()


def test_implemented_by_decorations7(mocker):
    tomcat = tm.TomcatManager()
    cmock = mocker.patch(
        "tomcatmanager.tomcat_manager.TomcatManager.is_connected",
        new_callable=mock.PropertyMock,
    )
    cmock.return_value = True
    vmock = mocker.patch(
        "tomcatmanager.tomcat_manager.TomcatManager.tomcat_major",
        new_callable=mock.PropertyMock,
    )
    vmock.return_value = tm.TomcatMajor.V7
    # don't care if this errors because all we care is that the decorator
    # allowed us to try and make a HTTP request. Functionality of the
    # decorated method is tested elsewhere
    gmock = mocker.patch("requests.get")
    gmock.side_effect = requests.HTTPError

    with pytest.raises(ValueError):
        tomcat.deploy_localwar(None, None)
    with pytest.raises(ValueError):
        tomcat.deploy_serverwar(None, None)
    with pytest.raises(ValueError):
        tomcat.deploy_servercontext(None, None)
    with pytest.raises(ValueError):
        tomcat.undeploy(None)
    with pytest.raises(ValueError):
        tomcat.start(None)
    with pytest.raises(ValueError):
        tomcat.stop(None)
    with pytest.raises(ValueError):
        tomcat.reload(None)
    with pytest.raises(ValueError):
        tomcat.sessions(None)
    with pytest.raises(ValueError):
        tomcat.expire(None)
    with pytest.raises(requests.HTTPError):
        response = tomcat.list()
    assert gmock.call_count == 1
    with pytest.raises(requests.HTTPError):
        response = tomcat.server_info()
    assert gmock.call_count == 2
    with pytest.raises(requests.HTTPError):
        response = tomcat.status_xml()
    assert gmock.call_count == 3
    with pytest.raises(requests.HTTPError):
        response = tomcat.vm_info()
    assert gmock.call_count == 4
    with pytest.raises(requests.HTTPError):
        response = tomcat.thread_dump()
    assert gmock.call_count == 5
    with pytest.raises(requests.HTTPError):
        response = tomcat.resources()
    assert gmock.call_count == 6
    with pytest.raises(requests.HTTPError):
        response = tomcat.find_leakers()
    assert gmock.call_count == 7


def test_implemented_by_decorations8(mocker):
    tomcat = tm.TomcatManager()
    cmock = mocker.patch(
        "tomcatmanager.tomcat_manager.TomcatManager.is_connected",
        new_callable=mock.PropertyMock,
    )
    cmock.return_value = True
    vmock = mocker.patch(
        "tomcatmanager.tomcat_manager.TomcatManager.tomcat_major",
        new_callable=mock.PropertyMock,
    )
    vmock.return_value = tm.TomcatMajor.V8
    # don't care if this errors because all we care is that the decorator
    # allowed us to try and make a HTTP request. Functionality of the
    # decorated method is tested elsewhere
    gmock = mocker.patch("requests.get")
    gmock.side_effect = requests.HTTPError

    with pytest.raises(ValueError):
        tomcat.deploy_localwar(None, None)
    with pytest.raises(ValueError):
        tomcat.deploy_serverwar(None, None)
    with pytest.raises(ValueError):
        tomcat.deploy_servercontext(None, None)
    with pytest.raises(ValueError):
        tomcat.undeploy(None)
    with pytest.raises(ValueError):
        tomcat.start(None)
    with pytest.raises(ValueError):
        tomcat.stop(None)
    with pytest.raises(ValueError):
        tomcat.reload(None)
    with pytest.raises(ValueError):
        tomcat.sessions(None)
    with pytest.raises(ValueError):
        tomcat.expire(None)
    with pytest.raises(requests.HTTPError):
        response = tomcat.list()
    assert gmock.call_count == 1
    with pytest.raises(requests.HTTPError):
        response = tomcat.ssl_connector_ciphers()
    assert gmock.call_count == 2
    with pytest.raises(requests.HTTPError):
        response = tomcat.server_info()
    assert gmock.call_count == 3
    with pytest.raises(requests.HTTPError):
        response = tomcat.status_xml()
    assert gmock.call_count == 4
    with pytest.raises(requests.HTTPError):
        response = tomcat.vm_info()
    assert gmock.call_count == 5
    with pytest.raises(requests.HTTPError):
        response = tomcat.thread_dump()
    assert gmock.call_count == 6
    with pytest.raises(requests.HTTPError):
        response = tomcat.resources()
    assert gmock.call_count == 7
    with pytest.raises(requests.HTTPError):
        response = tomcat.find_leakers()
    assert gmock.call_count == 8


TOMCAT_MAJORS = [
    tm.TomcatMajor.V9,
    tm.TomcatMajor.V10,
    tm.TomcatMajor.VNEXT,
]


METHOD_MATRIX = [
    # ( method name, number of arguments, expected exception )
    ("deploy_localwar", 2, ValueError),
    ("deploy_serverwar", 2, ValueError),
    ("deploy_servercontext", 2, ValueError),
    ("undeploy", 1, ValueError),
    ("start", 1, ValueError),
    ("stop", 1, ValueError),
    ("reload", 1, ValueError),
    ("sessions", 1, ValueError),
    ("expire", 1, ValueError),
    ("list", 0, requests.HTTPError),
    ("ssl_connector_ciphers", 0, requests.HTTPError),
    ("ssl_connector_certs", 0, requests.HTTPError),
    ("ssl_connector_trusted_certs", 0, requests.HTTPError),
    ("ssl_reload", 0, requests.HTTPError),
    ("server_info", 0, requests.HTTPError),
    ("status_xml", 0, requests.HTTPError),
    ("vm_info", 0, requests.HTTPError),
    ("thread_dump", 0, requests.HTTPError),
    ("resources", 0, requests.HTTPError),
    ("find_leakers", 0, requests.HTTPError),
]


@pytest.mark.parametrize("tomcat_major", TOMCAT_MAJORS)
@pytest.mark.parametrize("method, arg_count, exc", METHOD_MATRIX)
def test_implemented_by_decorations_short(mocker, tomcat_major, arg_count, method, exc):
    tomcat = tm.TomcatManager()
    cmock = mocker.patch(
        "tomcatmanager.tomcat_manager.TomcatManager.is_connected",
        new_callable=mock.PropertyMock,
    )
    cmock.return_value = True
    vmock = mocker.patch(
        "tomcatmanager.tomcat_manager.TomcatManager.tomcat_major",
        new_callable=mock.PropertyMock,
    )
    vmock.return_value = tomcat_major
    # don't care if this errors because all we care is that the decorator
    # allowed us to try and make a HTTP request. Functionality of the
    # decorated method is tested elsewhere
    gmock = mocker.patch("requests.get")
    gmock.side_effect = requests.HTTPError

    with pytest.raises(exc):
        method = getattr(tomcat, method)
        if arg_count == 2:
            method(None, None)
        elif arg_count == 1:
            method(None)
        else:
            method()
