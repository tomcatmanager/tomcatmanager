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
import io
import pytest

import tomcatmanager as tm

from test_manager import TestManagerBase


###
#
# test the action commands, i.e. commands that actually effect some change on
# the server
#
###
class TestAction(TestManagerBase):

	def test_expire_no_path(self, tomcat):
		"""expire requires a path"""
		r = tomcat.expire('', 0)
		self.failure_assertions(r)

	def test_expire(self, tomcat):
		r = tomcat.expire('/manager', 10)
		self.info_assertions(r)
		assert r.result == r.sessions

	def test_start_no_path(self, tomcat):
		"""start requires a path"""
		r = tomcat.start(None)
		self.failure_assertions(r)

	def test_start(self, tomcat):
		r = tomcat.start('/someapp')
		self.success_assertions(r)

	def test_stop_no_path(self, tomcat):
		"""stop requires a path"""
		r = tomcat.start(None)
		self.failure_assertions(r)

	def test_stop(self, tomcat):
		r = tomcat.stop('/someapp')
		self.success_assertions(r)

	def test_reload_no_path(self, tomcat):
		"""reload requires a path"""
		r = tomcat.reload(None)
		self.failure_assertions(r)

	def test_reload(self, tomcat):
		r = tomcat.reload('/someapp')
		self.success_assertions(r)

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
	
	def test_deploy_no_args(self, tomcat):
		r = tomcat.deploy()
		self.failure_assertions(r)

	def test_deploy_local_war(self, tomcat, war_fileobj):
		r = tomcat.deploy(path='/newapp', war=war_fileobj)
		self.success_assertions(r)

	def test_deploy_local_war_tag(self, tomcat, war_fileobj):
		r = tomcat.deploy(path='/newapp', war=war_fileobj, tag='mytag')
		self.success_assertions(r)

	def test_deploy_local_war_update(self, tomcat, war_fileobj):
		r = tomcat.deploy(path='/newapp', war=war_fileobj, update=True)
		self.success_assertions(r)

	def test_deploy_local_war_tag_update(self, tomcat, war_fileobj):
		r = tomcat.deploy(path='/newapp', war=war_fileobj, tag='mytag', update=True)
		self.success_assertions(r)

	def test_undeploy_no_path(self, tomcat):
		"""ensure we throw an exception if we don't have a path to undeploy"""
		r = tomcat.undeploy(None)
		self.failure_assertions(r)
	
	def test_undeploy(self, tomcat):
		"""should throw an exception if there is an error"""
		r = tomcat.undeploy('/newapp')
		self.success_assertions(r)
