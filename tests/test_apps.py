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
# test the methods for managing applications on the server
#
###
class TestApps(TestManagerBase):

    ###
    #
    # deploy
    #
    ###
    def test_deploy_path_only(self, tomcat):
        r = tomcat.deploy(path=self.safe_path)
        self.failure_assertions(r)  
    
    def test_deploy_localwar_no_path(self, tomcat, war_fileobj):
        r = tomcat.deploy(None, localwar=war_fileobj)
        self.failure_assertions(r)
        r = tomcat.deploy('', localwar=war_fileobj)
        self.failure_assertions(r)

    def test_deploy_localwar(self, tomcat, war_fileobj):
        r = tomcat.deploy(path=self.safe_path, localwar=war_fileobj)
        self.success_assertions(r)
        r = tomcat.undeploy(path=self.safe_path)
        self.success_assertions(r)

    def test_deploy_localwar_version(self, tomcat, war_fileobj):
        r = tomcat.deploy(path=self.safe_path, localwar=war_fileobj, version='42')
        self.success_assertions(r)
        r = tomcat.undeploy(path=self.safe_path, version='42')
        self.success_assertions(r)
    
    def test_deploy_localwar_update(self, tomcat, war_fileobj):
        r = tomcat.deploy(path=self.safe_path, localwar=war_fileobj, update=True)
        self.success_assertions(r)
        r = tomcat.undeploy(path=self.safe_path)
        self.success_assertions(r)

    def test_deploy_localwar_version_update(self, tomcat, war_fileobj):
        r = tomcat.deploy(path=self.safe_path, localwar=war_fileobj, version='42', update=True)
        self.success_assertions(r)
        r = tomcat.undeploy(path=self.safe_path, version='42')
        self.success_assertions(r)

    def test_deploy_serverwar_and_localwar(self, tomcat, war_fileobj):
        with pytest.raises(ValueError):
            r = tomcat.deploy(self.safe_path, localwar=war_fileobj, serverwar='/path/to/foo.war')

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
        r = tomcat.deploy('', serverwar='/path/to/foo.war')
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

    ###
    #
    # undeploy
    #
    ###
    def test_undeploy_no_path(self, tomcat):
        """ensure we throw an exception if we don't have a path to undeploy"""
        r = tomcat.undeploy(None)
        self.failure_assertions(r)
        r = tomcat.undeploy('')
        self.failure_assertions(r)        

    ###
    #
    # start and stop
    #
    ###
    def test_start_no_path(self, tomcat):
        """start requires a path"""
        r = tomcat.start(None)
        self.failure_assertions(r)
        r = tomcat.start('')
        self.failure_assertions(r)

    def test_stop_no_path(self, tomcat):
        """stop requires a path"""
        r = tomcat.stop(None)
        self.failure_assertions(r)
        r = tomcat.stop('')
        self.failure_assertions(r)

    def test_stop_start(self, tomcat, war_fileobj):
        r = tomcat.deploy(path=self.safe_path, localwar=war_fileobj)
        self.success_assertions(r)
        
        r = tomcat.stop(self.safe_path)
        self.success_assertions(r)

        r = tomcat.start(self.safe_path)
        self.success_assertions(r)

        r = tomcat.undeploy(path=self.safe_path)
        self.success_assertions(r)

    def test_stop_start_version(self, tomcat, war_fileobj):
        r = tomcat.deploy(path=self.safe_path, localwar=war_fileobj, version='42')
        self.success_assertions(r)
        
        r = tomcat.stop(self.safe_path, version='42')
        self.success_assertions(r)

        r = tomcat.start(self.safe_path, version='42')
        self.success_assertions(r)

        r = tomcat.undeploy(path=self.safe_path, version='42')
        self.success_assertions(r)
        
    
    ###
    #
    # reload
    #
    ###
    def test_reload_no_path(self, tomcat):
        """reload requires a path"""
        r = tomcat.reload(None)
        self.failure_assertions(r)
        # this reloads /
        r = tomcat.reload('')
        self.failure_assertions(r)

    def test_reload(self, tomcat, war_fileobj):
         r = tomcat.deploy(path=self.safe_path, localwar=war_fileobj)
         self.success_assertions(r)
        
         r = tomcat.reload(self.safe_path)
         self.success_assertions(r)

         r = tomcat.undeploy(path=self.safe_path)
         self.success_assertions(r)

    def test_reload_version(self, tomcat, war_fileobj):
        r = tomcat.deploy(path=self.safe_path, localwar=war_fileobj, version='42')
        self.success_assertions(r)
        
        r = tomcat.reload(self.safe_path, version='42')
        self.success_assertions(r)

        r = tomcat.undeploy(path=self.safe_path, version='42')
        self.success_assertions(r)


    ###
    #
    # sessions
    #
    ###
    def test_sessions_no_path(self, tomcat):
        """sessions requires a path"""
        r = tomcat.sessions(None)
        self.failure_assertions(r)
        # this gives sessions for /
        r = tomcat.sessions('')
        self.failure_assertions(r)
        
    def test_sessions(self, tomcat, war_fileobj):
        r = tomcat.deploy(path=self.safe_path, localwar=war_fileobj)
        self.success_assertions(r)
        
        r = tomcat.sessions(self.safe_path)
        self.info_assertions(r)
        assert r.result == r.sessions

        r = tomcat.undeploy(path=self.safe_path)
        self.success_assertions(r)


    def test_sessions_version(self, tomcat, war_fileobj):
        r = tomcat.deploy(path=self.safe_path, localwar=war_fileobj, version='42')
        self.success_assertions(r)
        
        r = tomcat.sessions(self.safe_path, version='42')
        self.info_assertions(r)
        assert r.result == r.sessions

        r = tomcat.undeploy(path=self.safe_path, version='42')
        self.success_assertions(r)
    
    ###
    #
    # expire
    #
    ###
    def test_expire_no_path(self, tomcat):
        """expire requires a path"""
        r = tomcat.expire(None)
        self.failure_assertions(r)
        # this expires /
        r = tomcat.expire('')
        self.failure_assertions(r)

    def test_expire(self, tomcat, war_fileobj):
        r = tomcat.deploy(path=self.safe_path, localwar=war_fileobj)
        self.success_assertions(r)
        
        r = tomcat.expire(self.safe_path, idle=30)
        self.info_assertions(r)
        assert r.result == r.sessions

        r = tomcat.undeploy(path=self.safe_path)
        self.success_assertions(r)

    def test_expire_version(self, tomcat, war_fileobj):
        r = tomcat.deploy(path=self.safe_path, localwar=war_fileobj, version='42')
        self.success_assertions(r)
        
        r = tomcat.expire(self.safe_path, version='42', idle=30)
        self.info_assertions(r)
        assert r.result == r.sessions

        r = tomcat.undeploy(path=self.safe_path, version='42')
        self.success_assertions(r)

    ###
    #
    # list
    #
    ###
    def test_list(self, tomcat):
        r = tomcat.list()
        self.info_assertions(r)
        assert isinstance(r.apps, list)
