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

import tomcatmanager as tm


class TestTomcatManagerResponse:

    def test_ok(self, tomcat):
        r = tomcat.list()
        assert r.ok

    def test_empty_http_response(self, tomcat):
        # say we get http response code 200, but tomcat doesn't
        # return a status line with OK or FAIL at the beginning
        with mock.patch('requests.models.Response.text', create=True,
                        new_callable=mock.PropertyMock) as mock_text:
            # chose a status value that won't raise an exception, but
            # that isn't 200, OK
            mock_text.return_value = None
            r = tomcat.vm_info()
            assert r.status_code is None
            assert r.status_message is None
            assert r.result is None

            mock_text.return_value = ''
            r = tomcat.vm_info()
            assert r.status_code is None
            assert r.status_message is None
            assert r.result is None

            mock_text.return_value = 'FAIL - some message'
            r = tomcat.vm_info()
            assert r.status_code == tm.codes.fail
            assert r.status_message == 'some message'
            assert r.result is None

            mock_text.return_value = 'OK - some message\nthe result'
            r = tomcat.vm_info()
            assert r.status_code == tm.codes.ok
            assert r.status_message == 'some message'
            assert r.result == 'the result'

            mock_text.return_value = 'malformedwithnospace'
            r = tomcat.vm_info()
            # we don't care what this is, but it better not be OK
            assert r.status_code != tm.codes.ok
            assert r.status_message is None
            assert r.result is None


class TestServerInfo:

    def test_dict(self, server_info):
        sinfo = tm.models.ServerInfo(server_info)
        assert sinfo['Tomcat Version'] == 'Apache Tomcat/8.0.32 (Ubuntu)'
        assert sinfo['OS Name'] == 'Linux'
        assert sinfo['OS Version'] == '4.4.0-89-generic'
        assert sinfo['OS Architecture'] == 'amd64'
        assert sinfo['JVM Version'] == '1.8.0_131-8u131-b11-2ubuntu1.16.04.3-b11'
        assert sinfo['JVM Vendor'] == 'Oracle Corporation'

    def test_properties(self, server_info):
        sinfo = tm.models.ServerInfo(server_info)
        assert sinfo.tomcat_version == 'Apache Tomcat/8.0.32 (Ubuntu)'
        assert sinfo.os_name == 'Linux'
        assert sinfo.os_version == '4.4.0-89-generic'
        assert sinfo.os_architecture == 'amd64'
        assert sinfo.jvm_version == '1.8.0_131-8u131-b11-2ubuntu1.16.04.3-b11'
        assert sinfo.jvm_vendor == 'Oracle Corporation'

    def test_parse_extra(self, server_info):
        lines = server_info + "New Key: New Value\n"
        sinfo = tm.models.ServerInfo(lines)
        assert sinfo['New Key'] == 'New Value'
