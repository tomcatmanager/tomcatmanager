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

from nose.tools import *
import requests
import tomcatmanager

from tests.mock_server import start_mock_server

class TestConnect:

	@classmethod
	def setup_class(cls):
		(cls.mock_url, cls.userid, cls.password) = start_mock_server()
	
	def test_connect(self):
		tm = tomcatmanager.TomcatManager(self.mock_url)
		assert_false(tm.is_connected())

		tm = tomcatmanager.TomcatManager(self.mock_url, self.userid, self.password)
		assert_true(tm.is_connected())

class TestManager:

	@classmethod
	def setup_class(cls):
		(cls.mock_url, cls.userid, cls.password) = start_mock_server()
		cls.tm = tomcatmanager.TomcatManager(cls.mock_url, cls.userid, cls.password)

	def test_serverinfo(self):
		assert_true(isinstance(self.tm.serverinfo(), dict))
