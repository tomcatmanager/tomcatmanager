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

import unittest
from nose.tools import *
import requests
import tomcatmanager
import io

from tests.mock_server import start_mock_server80

class TestConnect:

	@classmethod
	def setup_class(cls):
		(cls.mock_url, cls.userid, cls.password) = start_mock_server80()
	
	def test_connect(self):
		tm = tomcatmanager.TomcatManager(self.mock_url)
		assert_false(tm.is_connected())

		tm = tomcatmanager.TomcatManager(self.mock_url, self.userid, self.password)
		assert_true(tm.is_connected())

class TestManager(unittest.TestCase):

	@classmethod
	def setup_class(cls):
		(cls.mock_url, cls.userid, cls.password) = start_mock_server80()
		cls.tm = tomcatmanager.TomcatManager(cls.mock_url, cls.userid, cls.password)

	###
	#
	# test the info type commands, i.e. commands that don't really do anything, they
	# just return some information from the server
	#
	###
	def info_assertions(self, tmr):
		"""a set of common assertions that should be true of the info
		type commands which return a result"""
		# order matters here, we want to test the status_code before we
		# check for results. If the status_code is FAIL, then we probably
		# won't have the result we want, but we need to fix the FAIL instead
		# of worrying about why result it null
		assert_equal(tmr.status_code, 'OK', 'message from server: "{0}"'.format(tmr.status_message))
		assert_is_not_none(tmr.status_message)
		assert_true(len(tmr.status_message) > 0)
		try:
			tmr.raise_for_status()
		except RequestException as err:
			self.fail(err)
		except tomcatmanager.TomcatException as err:
			self.fail('TomcatException raised')

		assert_is_not_none(tmr.result)
		assert_true(len(tmr.result) > 0)

	def test_list(self):
		tmr = self.tm.list()
		self.info_assertions(tmr)
		assert_true(isinstance(tmr.apps, list))
	
	def test_server_info(self):
		tmr = self.tm.server_info()
		self.info_assertions(tmr)
		assert_is_instance(tmr.server_info, dict)

	def test_status_xml(self):
		tmr = self.tm.status_xml()
		self.info_assertions(tmr)
		assert_equal(tmr.result, tmr.status_xml)
		xml = tmr.status_xml
		assert_true(isinstance(xml, list))
		assert_equal(xml[0][:6], '<?xml ')

	def test_vm_info(self):
		tmr = self.tm.vm_info()
		self.info_assertions(tmr)

	def test_ssl_connector_ciphers(self):
		tmr = self.tm.ssl_connector_ciphers()
		self.info_assertions(tmr)
	
	def test_thread_dump(self):
		tmr = self.tm.thread_dump()
		self.info_assertions(tmr)
	
	def test_findleaks(self):
		pass


	###
	#
	# test the action commands, i.e. commands that actually effect some change on
	# the server
	#
	###
	@raises(tomcatmanager.TomcatException)
	def test_deploy_war_no_path(self):
		"""server should return FAIL if we don't have a path to deploy to"""
		warfile = io.BytesIO(b'the contents of my warfile')
		self.tm.deploy_war(None, warfile)

	def test_deploy_war(self):
		warfile = io.BytesIO(b'the contents of my warfile')
		self.tm.deploy_war('/newapp', warfile)

	@raises(tomcatmanager.TomcatException)
	def test_undeploy_no_path(self):
		"""server should return FAIL if we don't have a path to undeploy"""
		self.tm.undeploy(None)
	
	def test_undeploy(self):
		"""should throw an exception if there is an error"""
		self.tm.undeploy('/newapp')
