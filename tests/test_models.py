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

import pytest

import tomcatmanager as tm


class TestTomcatManagerResponse:
    
    def test_ok(self, tomcat):
        r = tomcat.list()
        assert r.ok == True

class TestServerInfo:

    def test_dict(self, server_info):
        s = tm.models.ServerInfo(server_info)
        assert s['Tomcat Version'] == 'Apache Tomcat/8.0.32 (Ubuntu)'
        assert s['OS Name'] == 'Linux'
        assert s['OS Version'] == '4.4.0-89-generic'
        assert s['OS Architecture'] == 'amd64'
        assert s['JVM Version'] == '1.8.0_131-8u131-b11-2ubuntu1.16.04.3-b11'
        assert s['JVM Vendor'] == 'Oracle Corporation'

    def test_properties(self, server_info):
        s = tm.models.ServerInfo(server_info)
        assert s.tomcat_version == 'Apache Tomcat/8.0.32 (Ubuntu)'
        assert s.os_name == 'Linux'
        assert s.os_version == '4.4.0-89-generic'
        assert s.os_architecture == 'amd64'
        assert s.jvm_version == '1.8.0_131-8u131-b11-2ubuntu1.16.04.3-b11'
        assert s.jvm_vendor == 'Oracle Corporation'

    def test_parse_extra(self, server_info):
        lines = server_info + "New Key: New Value\n"
        s = tm.models.ServerInfo(lines)
        assert s['New Key'] == 'New Value'
