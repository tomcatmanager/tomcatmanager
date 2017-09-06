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
from tests.test_manager import TestManagerBase


class TestInfo(TestManagerBase):
    """
    Test TomcatManager methods that retrieve info about the server.
    """

    def test_server_info(self, tomcat):
        r = tomcat.server_info()
        self.info_assertions(r)
        assert isinstance(r.server_info, tm.models.ServerInfo)

    def test_status_xml(self, tomcat):
        r = tomcat.status_xml()
        self.info_assertions(r)
        assert r.result == r.status_xml
        assert r.status_xml[:6] == '<?xml '

    def test_status_xml_fail(self, tomcat):
        with mock.patch('requests.models.Response.status_code', create=True,
                        new_callable=mock.PropertyMock) as mock_status:
            # chose a status value that won't raise an exception, but
            # that isn't 200, OK
            mock_status.return_value = 204 # No Content
            r = tomcat.status_xml()
            self.failure_assertions(r)
            assert r.status_code == tm.status_codes.fail

    def test_vm_info(self, tomcat):
        r = tomcat.vm_info()
        self.info_assertions(r)
        assert r.result == r.vm_info

    def test_ssl_connector_ciphers(self, tomcat):
        r = tomcat.ssl_connector_ciphers()
        self.info_assertions(r)
        assert r.result == r.ssl_connector_ciphers

    def test_thread_dump(self, tomcat):
        r = tomcat.thread_dump()
        self.info_assertions(r)
        assert r.result == r.thread_dump

    def test_resources_list(self, tomcat):
        r = tomcat.resources()
        self.info_assertions(r)
        assert isinstance(r.resources, dict)

    def test_resources_named_class(self, tomcat):
        r = tomcat.resources('org.apache.catalina.users.MemoryUserDatabase')
        self.info_assertions(r)
        assert isinstance(r.resources, dict)
        assert len(r.resources) == 1
        assert len(r.result.splitlines()) == len(r.resources)

    def test_resources_named_class_not_registered(self, tomcat):
        r = tomcat.resources('com.example.Nothing')
        self.info_assertions(r)
        assert isinstance(r.resources, dict)
        assert not r.resources

    def test_find_leakers(self, tomcat):
        r = tomcat.find_leakers()
        self.success_assertions(r)
        assert isinstance(r.leakers, list)

    def test_parse_leakers(self, tomcat):
        # _parse_leakers doesn't hit the server
        text = '/leaker1\n/leaker2\n'
        leakers = tomcat._parse_leakers(text)
        assert leakers == ['/leaker1', '/leaker2']

    def test_parse_leakers_duplicates(self, tomcat):
        text = '/leaker1\n/leaker2\n/leaker1\n/leaker3\n/leaker2\n'
        leakers = tomcat._parse_leakers(text)
        # make sure we don't have duplicates
        assert leakers == ['/leaker1', '/leaker2', '/leaker3']

    def test_parse_leakers_empty(self, tomcat):
        text = ''
        leakers = tomcat._parse_leakers(text)
        assert leakers == []

    def test_parse_leakers_none(self, tomcat):
        text = None
        leakers = tomcat._parse_leakers(text)
        assert leakers == []
