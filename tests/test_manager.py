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

import requests
import os
import io
import tomcatmanager as tm

from nose.tools import *
from nose.tools import with_setup
from tests.mock_server import start_mock_server80

###
#
# test the connect command
#
###
class TestConnect:

	@classmethod
	def setup_class(cls):
		(cls.mock_url, cls.userid, cls.password) = start_mock_server80()
	
	def test_connect(self):
		tomcat = tm.TomcatManager()
		assert_false(tomcat.is_connected)
		
		tomcat = tm.TomcatManager(self.mock_url)
		assert_false(tomcat.is_connected)

		tomcat = tm.TomcatManager(self.mock_url, self.userid, self.password)
		assert_true(tomcat.is_connected)

###
#
# test the info and action commands, except for deploy and undeploy
#
###
class TestManager:

	@classmethod
	def setup_class(cls):
		(cls.mock_url, cls.userid, cls.password) = start_mock_server80()
		cls.tomcat = tm.TomcatManager(cls.mock_url, cls.userid, cls.password)

	def success_assertions(self, tmr):
		"""a set of common assertions for every command to ensure it
		completed successfully"""
		assert_equal(tmr.status_code, tm.codes.ok, 'message from server: "{}"'.format(tmr.status_message))
		assert_is_not_none(tmr.status_message)
		assert_true(len(tmr.status_message) > 0)
		try:
			tmr.raise_for_status()
		except RequestException as err:
			self.fail(err)
		except TomcatError as err:
			self.fail(err)

	###
	#
	# test the info type commands, i.e. commands that don't really do anything, they
	# just return some information from the server
	#
	###
	def info_assertions(self, tmr):
		"""a set of common assertions that should be true of the info
		type commands which return a result"""
		self.success_assertions(tmr)
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

	def test_resources(self):
		tmr = self.tomcat.resources()
		self.info_assertions(tmr)
		assert_is_instance(tmr.resources, list)

		tmr = self.tomcat.resources('org.apache.catalina.users.MemoryUserDatabase')
		self.info_assertions(tmr)
		assert_is_instance(tmr.resources, list)
		assert_equal(len(tmr.resources), 1)
		
		tmr = self.tomcat.resources('com.example.Nothing')
		self.info_assertions(tmr)
		assert_is_instance(tmr.resources, list)
		assert_equal(len(tmr.resources), 0)
		

	def test_find_leakers(self):
		tmr = self.tomcat.find_leakers()
		self.success_assertions(tmr)
		
		assert_is_instance(tmr.leakers, list)
		# make sure we don't have duplicates
		assert_equal(len(tmr.leakers), len(set(tmr.leakers)))

	@raises(tm.TomcatError)
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
	@raises(tm.TomcatError)
	def test_expire_no_path(self):
		"""expire requires a path"""
		tmr = self.tomcat.expire('', 0)
		assert_equal(tmr.status_code, tm.codes.fail)
		tmr.raise_for_status()

	def test_expire(self):
		tmr = self.tomcat.expire('/manager', 10)
		self.info_assertions(tmr)
		assert_equal(tmr.result, tmr.sessions)

	@raises(tm.TomcatError)
	def test_start_no_path(self):
		"""start requires a path"""
		tmr = self.tomcat.start(None)
		assert_equal(tmr.status_code, tm.codes.fail)
		tmr.raise_for_status()

	def test_start(self):
		tmr = self.tomcat.start('/someapp')
		self.success_assertions(tmr)
		tmr.raise_for_status()

	@raises(tm.TomcatError)
	def test_stop_no_path(self):
		"""stop requires a path"""
		tmr = self.tomcat.start(None)
		assert_equal(tmr.status_code, tm.codes.fail)
		tmr.raise_for_status()

	def test_stop(self):
		tmr = self.tomcat.stop('/someapp')
		self.success_assertions(tmr)
		tmr.raise_for_status()

	@raises(tm.TomcatError)
	def test_reload_no_path(self):
		"""reload requires a path"""
		tmr = self.tomcat.reload(None)
		assert_equal(tmr.status_code, tm.codes.fail)
		tmr.raise_for_status()

	def test_reload(self):
		tmr = self.tomcat.reload('/someapp')
		self.success_assertions(tmr)
		tmr.raise_for_status()

###
#
# test the deploy command in all it's flavors
#
###

class TestDeploy(TestManager):
	"""here's the various flavors of deploy we need to support

		# local warfile to server, via PUT, all the rest via get
		tomcat.deploy(path='/sampleapp', war=fileobj)
		# deploy a previously deployed webapp which was deployed by a tag
		tomcat.deploy(path='/sampleapp', tag='footag')
		# deploy a warfile that's already on the server
		tomcat.deploy(path='/sampleapp', war='file:/path/to/foo')
		# implied path, deploys to /sampleapp
		tomcat.deploy(war='file:/path/to/sampleapp.war')
		# deploy from appBase sampleapp.war to context /sampleapp
		tomcat.deploy(war='sampleapp')
		# deploy from appBase sampleapp.war to context /sampleapp
		tomcat.deploy(war='sampleapp.war')
		# deploy based on a context.xml
		tomcat.deploy(config='file:/path/to/context.xml')
		# deploy by context and war
		tomcat.deploy(config='file:/path/to/context.xml', war='file:/path/bar.war')

		# ? see if we can deploy a config and a warfile
		tomcat.deploy(config='file:/path/to/context.xml', war=fileobj)		
	"""	

	###
	#
	# fixtures
	#
	###
	@classmethod
	def setup_class(cls):
		super().setup_class()
		cls.war_file = os.path.dirname(__file__) + '/war/sample.war'

	###
	#
	# tests
	#
	###
	def test_is_stream(self):
		war_fileobj = open(self.war_file, 'rb')
		assert_true(self.tomcat._is_stream(war_fileobj))
		
		fileobj = io.BytesIO(b'the contents of my warfile')
		assert_true(self.tomcat._is_stream(fileobj))
		
		assert_false(self.tomcat._is_stream(None))
		assert_false(self.tomcat._is_stream('some string'))
		assert_false(self.tomcat._is_stream(['some', 'list']))

	@raises(tm.TomcatError)
	def test_deploy_no_args(self):
		r = self.tomcat.deploy()
		assert_equal(r.status_code, tm.codes.fail)
		r.raise_for_status()

	def test_deploy_local_war(self):
		war_fileobj = open(self.war_file, 'rb')
		r = self.tomcat.deploy(path='/newapp', war=war_fileobj)
		self.success_assertions(r)
		r.raise_for_status()

	def test_deploy_local_war_tag(self):
		war_fileobj = open(self.war_file, 'rb')
		r = self.tomcat.deploy(path='/newapp', war=war_fileobj, tag='mytag')
		self.success_assertions(r)
		r.raise_for_status()

	def test_deploy_local_war_update(self):
		war_fileobj = open(self.war_file, 'rb')
		r = self.tomcat.deploy(path='/newapp', war=war_fileobj, update=True)
		self.success_assertions(r)
		r.raise_for_status()

	def test_deploy_local_war_tag_update(self):
		war_fileobj = open(self.war_file, 'rb')
		r = self.tomcat.deploy(path='/newapp', war=war_fileobj, tag='mytag', update=True)
		self.success_assertions(r)
		r.raise_for_status()

	@raises(tm.TomcatError)
	def test_undeploy_no_path(self):
		"""ensure we throw an exception if we don't have a path to undeploy"""
		r = self.tomcat.undeploy(None)
		assert_equal(r.status_code, tm.codes.fail)
		r.raise_for_status()
	
	def test_undeploy(self):
		"""should throw an exception if there is an error"""
		r = self.tomcat.undeploy('/newapp')
		self.success_assertions(r)
