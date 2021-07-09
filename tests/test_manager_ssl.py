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

from unittest import mock

import pytest

import tomcatmanager as tm


def test_ssl_connector_ciphers(tomcat, assert_tomcatresponse):
    if tomcat.implements(tomcat.ssl_connector_ciphers):
        r = tomcat.ssl_connector_ciphers()
        assert_tomcatresponse.info(r)
        assert r.result == r.ssl_connector_ciphers
    else:
        with pytest.raises(tm.TomcatNotImplementedError):
            r = tomcat.ssl_connector_ciphers()


def test_ssl_connector_certs(tomcat, assert_tomcatresponse):
    if tomcat.implements(tomcat.ssl_connector_certs):
        r = tomcat.ssl_connector_certs()
        assert_tomcatresponse.info(r)
        assert r.result == r.ssl_connector_certs
    else:
        with pytest.raises(tm.TomcatNotImplementedError):
            r = tomcat.ssl_connector_certs()


def test_ssl_connector_trusted_certs(tomcat, assert_tomcatresponse):
    if tomcat.implements(tomcat.ssl_connector_trusted_certs):
        r = tomcat.ssl_connector_trusted_certs()
        assert_tomcatresponse.info(r)
        assert r.result == r.ssl_connector_trusted_certs
    else:
        with pytest.raises(tm.TomcatNotImplementedError):
            r = tomcat.ssl_connector_trusted_certs()


def test_ssl_reload_success(tomcat, mocker, assert_tomcatresponse):
    # the command on the tomcat manager web app fails if SSL is not configured
    # we'll force it to be successful
    if tomcat.implements(tomcat.ssl_reload):
        mock_result = mocker.patch(
            "requests.Response.text", create=True, new_callable=mock.PropertyMock
        )
        mock_result.return_value = (
            "OK - Reloaded TLS configuration for [www.example.com]"
        )
        r = tomcat.ssl_reload("www.example.com")
        assert_tomcatresponse.success(r)
        assert r.status_message == "Reloaded TLS configuration for [www.example.com]"
    else:
        with pytest.raises(tm.TomcatNotImplementedError):
            r = tomcat.ssl_reload("www.example.com")


def test_ssl_reload_fail(tomcat, mocker, assert_tomcatresponse):
    # the command on the tomcat manager web app fails if SSL is not configured
    # we'll force it to fail
    if tomcat.implements(tomcat.ssl_reload):
        mock_result = mocker.patch(
            "requests.Response.text", create=True, new_callable=mock.PropertyMock
        )
        mock_result.return_value = "FAIL - Failed to reload TLS configuration"
        r = tomcat.ssl_reload()
        assert_tomcatresponse.failure(r)
        assert r.status_message == "Failed to reload TLS configuration"
    else:
        with pytest.raises(tm.TomcatNotImplementedError):
            r = tomcat.ssl_reload("www.example.com")
