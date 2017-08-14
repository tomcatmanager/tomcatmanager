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
        r = tomcat.expire('')
        self.failure_assertions(r)
        r = tomcat.expire(None)
        self.failure_assertions(r)

    def test_expire(self, tomcat):
        r = tomcat.expire('/manager', 30)
        self.info_assertions(r)
        assert r.result == r.sessions

    def test_expire_version(self, tomcat):
        r = tomcat.expire('/someapp', '5', 30)
        self.info_assertions(r)
        assert r.result == r.sessions

    def test_start_no_path(self, tomcat):
        """start requires a path"""
        r = tomcat.start(None)
        self.failure_assertions(r)

    def test_start(self, tomcat):
        r = tomcat.start('/someapp')
        self.success_assertions(r)

    def test_start_version(self, tomcat):
        r = tomcat.start('/someapp', '5')
        self.success_assertions(r)
        
    def test_stop_no_path(self, tomcat):
        """stop requires a path"""
        r = tomcat.start(None)
        self.failure_assertions(r)

    def test_stop(self, tomcat):
        r = tomcat.stop('/someapp')
        self.success_assertions(r)

    def test_stop_version(self, tomcat):
        r = tomcat.stop('/someapp', '5')
        self.success_assertions(r)      

    def test_reload_no_path(self, tomcat):
        """reload requires a path"""
        r = tomcat.reload(None)
        self.failure_assertions(r)

    def test_reload(self, tomcat):
        r = tomcat.reload('/someapp')
        self.success_assertions(r)

    def test_reload_version(self, tomcat):
        r = tomcat.reload('/someapp', '5')
        self.success_assertions(r)

    ###
    #
    # test deploy variations
    #
    ###
    def test_deploy_path_only(self, tomcat):
        r = tomcat.deploy(path='/newapp')
        self.failure_assertions(r)  
    
    def test_deploy_localwar_no_path(self, tomcat, war_fileobj):
        r = tomcat.deploy(None, localwar=war_fileobj)
        self.failure_assertions(r)

    def test_deploy_localwar(self, tomcat, war_fileobj):
        r = tomcat.deploy(path='/newapp', localwar=war_fileobj)
        self.success_assertions(r)

    def test_deploy_localwar_version(self, tomcat, war_fileobj):
        r = tomcat.deploy(path='/newapp', localwar=war_fileobj, version='42')
        self.success_assertions(r)
    
    def test_deploy_localwar_update(self, tomcat, war_fileobj):
        r = tomcat.deploy(path='/newapp', localwar=war_fileobj, update=True)
        self.success_assertions(r)

    def test_deploy_localwar_version_update(self, tomcat, war_fileobj):
        r = tomcat.deploy(path='/newapp', localwar=war_fileobj, version='42', update=True)
        self.success_assertions(r)

    def test_deploy_serverwar_and_localwar(self, tomcat, war_fileobj):
        with pytest.raises(ValueError):
            r = tomcat.deploy('/newapp', localwar=war_fileobj, serverwar='/path/to/foo.war')
    
    def test_deploy_serverwar_no_path(self, tomcat):
        """deploy a war from a file on the server without a path
        
        https://tomcat.apache.org/tomcat-8.0-doc/manager-howto.html#Deploy_A_New_Application_from_a_Local_Path
        says that you should be able to just deploy a war file, but testing indicates
        that you must have a path as well
        
        therefore, this should be a failure even though the documentation says it should
        work
        """
        r = tomcat.deploy(None, serverwar='/path/to/foo.war')
        self.failure_assertions(r)

    def test_deploy_serverwar_update(self, tomcat, war_fileobj):
        r = tomcat.deploy(path='/newapp', serverwar=war_fileobj, update=True)
        self.success_assertions(r)
    
    def test_deploy_serverwar(self, tomcat):
        r = tomcat.deploy(path='/newapp', serverwar='/path/to/foo.war')
        self.success_assertions(r)

    def test_deploy_serverwar_version(self, tomcat):
        r = tomcat.deploy(path='/newapp', serverwar='/path/to/foo.war', version='42')
        self.success_assertions(r)

    def test_deploy_serverwar_update(self, tomcat):
        r = tomcat.deploy(path='/newapp', serverwar='/path/to/foo.war', update=True)
        self.success_assertions(r)
    
    def test_deploy_serverwar_version_update(self, tomcat):
        r = tomcat.deploy(path='/newapp', serverwar='/path/to/foo.war', version='42', update=True)
        self.success_assertions(r)
    
    def test_undeploy_no_path(self, tomcat):
        """ensure we throw an exception if we don't have a path to undeploy"""
        r = tomcat.undeploy(None)
        self.failure_assertions(r)
    
    def test_undeploy(self, tomcat):
        """should throw an exception if there is an error"""
        r = tomcat.undeploy('/newapp')
        self.success_assertions(r)

    def test_undeploy_version(self, tomcat):
        r = tomcat.undeploy('/newapp', '3')
        self.success_assertions(r)
