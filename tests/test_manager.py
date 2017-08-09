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
import io
import tomcatmanager as tm

from tests.mock_server import start_mock_server80

class TestConnect:

	@classmethod
	def setup_class(cls):
		(cls.mock_url, cls.userid, cls.password) = start_mock_server80()
	
	def test_connect(self):
		tomcat = tm.TomcatManager(self.mock_url)
		assert_false(tomcat.is_connected())

		tomcat = tm.TomcatManager(self.mock_url, self.userid, self.password)
		assert_true(tomcat.is_connected())

class TestManager(unittest.TestCase):

	@classmethod
	def setup_class(cls):
		(cls.mock_url, cls.userid, cls.password) = start_mock_server80()
		cls.tomcat = tm.TomcatManager(cls.mock_url, cls.userid, cls.password)

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
		assert_equal(tmr.status_code, tm.codes.ok, 'message from server: "{0}"'.format(tmr.status_message))
		assert_is_not_none(tmr.status_message)
		assert_true(len(tmr.status_message) > 0)
		try:
			tmr.raise_for_status()
		except RequestException as err:
			self.fail(err)
		except TomcatException as err:
			self.fail('TomcatException raised')

		assert_is_not_none(tmr.result)
		assert_true(len(tmr.result) > 0)

	def test_list(self):
		tmr = self.tomcat.list()
		self.info_assertions(tmr)
		assert_true(isinstance(tmr.apps, list))
	
	def test_server_info(self):
		tmr = self.tomcat.server_info()
		self.info_assertions(tmr)
		assert_is_instance(tmr.server_info, dict)

	def test_status_xml(self):
		tmr = self.tomcat.status_xml()
		self.info_assertions(tmr)
		assert_equal(tmr.result, tmr.status_xml)
		xml = tmr.status_xml
		assert_is_instance(xml, list)
		assert_equal(xml[0][:6], '<?xml ')

	def test_vm_info(self):
		tmr = self.tomcat.vm_info()
		self.info_assertions(tmr)
		assert_equal(tmr.result, tmr.vm_info)

	def test_ssl_connector_ciphers(self):
		tmr = self.tomcat.ssl_connector_ciphers()
		self.info_assertions(tmr)
		assert_equal(tmr.result, tmr.ssl_connector_ciphers)
	
	def test_thread_dump(self):
		tmr = self.tomcat.thread_dump()
		self.info_assertions(tmr)
		assert_equal(tmr.result, tmr.thread_dump)

	def test_find_leakers(self):
		tmr = self.tomcat.find_leakers()
		# don't use info_assertions() because there might not be any leakers
		assert_equal(tmr.status_code, tm.codes.ok, 'message from server: "{0}"'.format(tmr.status_message))
		assert_is_not_none(tmr.status_message)
		assert_true(len(tmr.status_message) > 0)
		try:
			tmr.raise_for_status()
		except RequestException as err:
			self.fail(err)
		except TomcatException as err:
			self.fail('unexpected TomcatException raised')
		
		assert_is_instance(tmr.leakers, list)
		# make sure we don't have duplicates
		assert_equal(len(tmr.leakers), len(set(tmr.leakers)))

	@raises(tm.TomcatException)
	def test_sessions_no_path(self):	
		"""sessions requires a path"""
		tmr = self.tomcat.sessions('')
		assert_equal(tmr.status_code, tm.codes.fail)
		tmr.raise_for_status()

	def test_sessions(self):
		tmr = self.tomcat.sessions('/manager')
		self.info_assertions(tmr)
		assert_equal(tmr.result, tmr.sessions)

	###
	#
	# test the action commands, i.e. commands that actually effect some change on
	# the server
	#
	###
	@raises(tm.TomcatException)
	def test_expire_no_path(self):
		"""expire requires a path"""
		tmr = self.tomcat.expire('', 0)
		assert_equal(tmr.status_code, tm.codes.fail)
		tmr.raise_for_status()

	def test_expire(self):
		tmr = self.tomcat.expire('/manager', 10)
		self.info_assertions(tmr)
		assert_equal(tmr.result, tmr.sessions)

	@raises(tm.TomcatException)
	def test_start_no_path(self):
		"""start requires a path"""
		tmr = self.tomcat.start(None)
		assert_equal(tmr.status_code, tm.codes.fail)
		tmr.raise_for_status()

	def test_start(self):
		tmr = self.tomcat.start('/someapp')
		assert_equal(tmr.status_code, tm.codes.ok)
		tmr.raise_for_status()

	@raises(tm.TomcatException)
	def test_stop_no_path(self):
		"""stop requires a path"""
		tmr = self.tomcat.start(None)
		assert_equal(tmr.status_code, tm.codes.fail)
		tmr.raise_for_status()

	def test_stop(self):
		tmr = self.tomcat.stop('/someapp')
		assert_equal(tmr.status_code, tm.codes.ok)
		tmr.raise_for_status()

	@raises(tm.TomcatException)
	def test_reload_no_path(self):
		"""reload requires a path"""
		tmr = self.tomcat.reload(None)
		assert_equal(tmr.status_code, tm.codes.fail)
		tmr.raise_for_status()

	def test_reload(self):
		tmr = self.tomcat.reload('/someapp')
		assert_equal(tmr.status_code, tm.codes.ok)
		tmr.raise_for_status()
	
	@raises(tm.TomcatException)
	def test_deploy_war_no_path(self):
		"""ensure we throw an exception if we don't have a path to deploy to"""
		warfile = io.BytesIO(b'the contents of my warfile')
		self.tomcat.deploy_war(None, warfile)

	def test_deploy_war(self):
		warfile = io.BytesIO(b'the contents of my warfile')
		self.tomcat.deploy_war('/newapp', warfile)

	@raises(tm.TomcatException)
	def test_undeploy_no_path(self):
		"""ensure we throw an exception if we don't have a path to undeploy"""
		self.tomcat.undeploy(None)
	
	def test_undeploy(self):
		"""should throw an exception if there is an error"""
		self.tomcat.undeploy('/newapp')
