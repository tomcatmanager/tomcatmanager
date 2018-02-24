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

from tests.test_manager import TestManagerBase
import tomcatmanager as tm


class TestApps(TestManagerBase):
    """
    Test TomcatManager methods related to Tomcat applications.
    """

    ###
    #
    # deploy localwar
    #
    ###
    def test_deploy_localwar_path_only(self, tomcat, safe_path):
        with pytest.raises(ValueError):
            r = tomcat.deploy_localwar(safe_path, None)
        with pytest.raises(ValueError):
            r = tomcat.deploy_localwar(safe_path, '')

    def test_deploy_localwar_warfile_only(self, tomcat, localwar_file):
        with pytest.raises(ValueError):
            r = tomcat.deploy_localwar(None, localwar_file)
        with pytest.raises(ValueError):
            r = tomcat.deploy_localwar('', localwar_file)

    def test_deploy_localwar(self, tomcat, localwar_file, safe_path):
        r = tomcat.deploy_localwar(safe_path, localwar_file)
        self.success_assertions(r)
        r = tomcat.undeploy(safe_path)
        self.success_assertions(r)

    def test_deploy_localwar_fileobj(self, tomcat, localwar_file, safe_path):
        with open(localwar_file, 'rb') as localwar_fileobj:
            r = tomcat.deploy_localwar(safe_path, localwar_fileobj)
            self.success_assertions(r)
        r = tomcat.undeploy(safe_path)
        self.success_assertions(r)

    def test_deploy_localwar_version(self, tomcat, localwar_file, safe_path):
        r = tomcat.deploy_localwar(safe_path, localwar_file, version='42')
        self.success_assertions(r)
        r = tomcat.undeploy(safe_path, version='42')
        self.success_assertions(r)

    def test_deploy_localwar_update(self, tomcat, localwar_file, safe_path):
        r = tomcat.deploy_localwar(safe_path, localwar_file)
        self.success_assertions(r)
        r = tomcat.deploy_localwar(safe_path, localwar_file, update=True)
        self.success_assertions(r)
        r = tomcat.undeploy(safe_path)
        self.success_assertions(r)

    def test_deploy_localwar_version_update(self, tomcat, localwar_file, safe_path):
        r = tomcat.deploy_localwar(safe_path, localwar_file, version='42')
        self.success_assertions(r)
        r = tomcat.deploy_localwar(safe_path, localwar_file, version='42', update=True)
        self.success_assertions(r)
        r = tomcat.undeploy(safe_path, version='42')
        self.success_assertions(r)

    ###
    #
    # deploy serverwar
    #
    ###
    def test_deploy_serverwar_path_only(self, tomcat, safe_path):
        with pytest.raises(ValueError):
            r = tomcat.deploy_serverwar(safe_path, None)
        with pytest.raises(ValueError):
            r = tomcat.deploy_serverwar(safe_path, '')

    def test_deploy_serverwar_warfile_only(self, tomcat, tomcat_manager_server):
        with pytest.raises(ValueError):
            r = tomcat.deploy_serverwar(None, tomcat_manager_server.warfile)
        with pytest.raises(ValueError):
            r = tomcat.deploy_serverwar('', tomcat_manager_server.warfile)

    def test_deploy_serverwar(self, tomcat, tomcat_manager_server, safe_path):
        r = tomcat.deploy_serverwar(safe_path, tomcat_manager_server.warfile)
        self.success_assertions(r)
        r = tomcat.undeploy(safe_path)
        self.success_assertions(r)

    def test_deploy_serverwar_version(self, tomcat, tomcat_manager_server, safe_path):
        r = tomcat.deploy_serverwar(safe_path, tomcat_manager_server.warfile, version='42')
        self.success_assertions(r)
        r = tomcat.undeploy(safe_path, version='42')
        self.success_assertions(r)

    def test_deploy_serverwar_update(self, tomcat, tomcat_manager_server, safe_path):
        r = tomcat.deploy_serverwar(safe_path, tomcat_manager_server.warfile)
        self.success_assertions(r)
        r = tomcat.deploy_serverwar(safe_path, tomcat_manager_server.warfile, update=True)
        self.success_assertions(r)
        r = tomcat.undeploy(safe_path)
        self.success_assertions(r)

    def test_deploy_serverwar_version_update(self, tomcat, tomcat_manager_server, safe_path):
        r = tomcat.deploy_serverwar(safe_path, tomcat_manager_server.warfile, version='42')
        self.success_assertions(r)
        r = tomcat.deploy_serverwar(safe_path, tomcat_manager_server.warfile, version='42', update=True)
        self.success_assertions(r)
        r = tomcat.undeploy(safe_path, version='42')
        self.success_assertions(r)

    ###
    #
    # deploy servercontext
    #
    ###
    def test_deploy_servercontext_path_only(self, tomcat, safe_path):
        with pytest.raises(ValueError):
            r = tomcat.deploy_servercontext(safe_path, None)
        with pytest.raises(ValueError):
            r = tomcat.deploy_servercontext(safe_path, '')

    def test_deploy_servercontext_contextfile_only(self, tomcat, tomcat_manager_server):
        with pytest.raises(ValueError):
            r = tomcat.deploy_servercontext(None, tomcat_manager_server.contextfile)
        with pytest.raises(ValueError):
            r = tomcat.deploy_servercontext('', tomcat_manager_server.contextfile)

    def test_deploy_servercontext_contextfile_and_war_only(self, tomcat, tomcat_manager_server):
        with pytest.raises(ValueError):
            r = tomcat.deploy_servercontext(
                None,
                tomcat_manager_server.contextfile,
                warfile=tomcat_manager_server.warfile
            )
        with pytest.raises(ValueError):
            r = tomcat.deploy_servercontext('', tomcat_manager_server.contextfile)

    def test_deploy_servercontext(self, tomcat, tomcat_manager_server, safe_path):
        r = tomcat.deploy_servercontext(safe_path, tomcat_manager_server.contextfile)
        self.success_assertions(r)
        r = tomcat.undeploy(safe_path)
        self.success_assertions(r)

    def test_deploy_servercontext_update(self, tomcat, tomcat_manager_server, safe_path):
        r = tomcat.deploy_servercontext(safe_path, tomcat_manager_server.contextfile)
        self.success_assertions(r)
        r = tomcat.deploy_servercontext(safe_path, tomcat_manager_server.contextfile, update=True)
        self.success_assertions(r)
        r = tomcat.undeploy(safe_path)
        self.success_assertions(r)

    def test_deploy_servercontext_version(self, tomcat, tomcat_manager_server, safe_path):
        r = tomcat.deploy_servercontext(safe_path, tomcat_manager_server.contextfile, version='42')
        self.success_assertions(r)
        r = tomcat.undeploy(safe_path, version='42')
        self.success_assertions(r)

    def test_deploy_servercontext_version_update(self, tomcat, tomcat_manager_server, safe_path):
        r = tomcat.deploy_servercontext(safe_path, tomcat_manager_server.contextfile, version='42')
        self.success_assertions(r)
        r = tomcat.deploy_servercontext(safe_path, tomcat_manager_server.contextfile, version='42', update=True)
        self.success_assertions(r)
        r = tomcat.undeploy(safe_path, version='42')
        self.success_assertions(r)

    def test_deploy_servercontext_warfile(self, tomcat, tomcat_manager_server, safe_path):
        r = tomcat.deploy_servercontext(safe_path, tomcat_manager_server.contextfile, tomcat_manager_server.warfile)
        self.success_assertions(r)
        r = tomcat.undeploy(safe_path)
        self.success_assertions(r)

    def test_deploy_servercontext_warfile_update(self, tomcat, tomcat_manager_server, safe_path):
        r = tomcat.deploy_servercontext(safe_path, tomcat_manager_server.contextfile, tomcat_manager_server.warfile)
        self.success_assertions(r)
        r = tomcat.deploy_servercontext(safe_path, tomcat_manager_server.contextfile, tomcat_manager_server.warfile, update=True)
        self.success_assertions(r)
        r = tomcat.undeploy(safe_path)
        self.success_assertions(r)

    def test_deploy_servercontext_warfile_version(self, tomcat, tomcat_manager_server, safe_path):
        r = tomcat.deploy_servercontext(safe_path, tomcat_manager_server.contextfile, tomcat_manager_server.warfile, version='42')
        self.success_assertions(r)
        r = tomcat.undeploy(safe_path, version='42')
        self.success_assertions(r)

    def test_deploy_servercontext_warfile_version_update(self, tomcat, tomcat_manager_server, safe_path):
        r = tomcat.deploy_servercontext(safe_path, tomcat_manager_server.contextfile, tomcat_manager_server.warfile, version='42')
        self.success_assertions(r)
        r = tomcat.deploy_servercontext(safe_path, tomcat_manager_server.contextfile, tomcat_manager_server.warfile, version='42', update=True)
        self.success_assertions(r)
        r = tomcat.undeploy(safe_path, version='42')
        self.success_assertions(r)

    ###
    #
    # undeploy
    #
    ###
    def test_undeploy_no_path(self, tomcat):
        with pytest.raises(ValueError):
            r = tomcat.undeploy(None)
        with pytest.raises(ValueError):
            r = tomcat.undeploy('')

    ###
    #
    # start and stop
    #
    ###
    def test_start_no_path(self, tomcat):
        with pytest.raises(ValueError):
            r = tomcat.start(None)
        with pytest.raises(ValueError):
            r = tomcat.start('')

    def test_stop_no_path(self, tomcat):
        with pytest.raises(ValueError):
            r = tomcat.stop(None)
        with pytest.raises(ValueError):
            r = tomcat.stop('')

    def test_stop_start(self, tomcat, localwar_file, safe_path):
        with open(localwar_file, 'rb') as localwar_fileobj:
            r = tomcat.deploy_localwar(safe_path, localwar_fileobj)
        self.success_assertions(r)

        r = tomcat.stop(safe_path)
        self.success_assertions(r)

        r = tomcat.start(safe_path)
        self.success_assertions(r)

        r = tomcat.undeploy(safe_path)
        self.success_assertions(r)

    def test_stop_start_version(self, tomcat, localwar_file, safe_path):
        r = tomcat.deploy_localwar(safe_path, localwar_file, version='42')
        self.success_assertions(r)

        r = tomcat.stop(safe_path, version='42')
        self.success_assertions(r)

        r = tomcat.start(safe_path, version='42')
        self.success_assertions(r)

        r = tomcat.undeploy(safe_path, version='42')
        self.success_assertions(r)


    ###
    #
    # reload
    #
    ###
    def test_reload_no_path(self, tomcat):
        with pytest.raises(ValueError):
            r = tomcat.reload(None)
        with pytest.raises(ValueError):
            r = tomcat.reload('')

    def test_reload(self, tomcat, localwar_file, safe_path):
        r = tomcat.deploy_localwar(safe_path, localwar_file)
        self.success_assertions(r)

        r = tomcat.reload(safe_path)
        self.success_assertions(r)

        r = tomcat.undeploy(safe_path)
        self.success_assertions(r)

    def test_reload_version(self, tomcat, localwar_file, safe_path):
        r = tomcat.deploy_localwar(safe_path, localwar_file, version='42')
        self.success_assertions(r)

        r = tomcat.reload(safe_path, version='42')
        self.success_assertions(r)

        r = tomcat.undeploy(safe_path, version='42')
        self.success_assertions(r)


    ###
    #
    # sessions
    #
    ###
    def test_sessions_no_path(self, tomcat):
        with pytest.raises(ValueError):
            r = tomcat.sessions(None)
        with pytest.raises(ValueError):
            r = tomcat.sessions('')

    def test_sessions(self, tomcat, localwar_file, safe_path):
        r = tomcat.deploy_localwar(safe_path, localwar_file)
        self.success_assertions(r)

        r = tomcat.sessions(safe_path)
        self.info_assertions(r)
        assert r.result == r.sessions

        r = tomcat.undeploy(safe_path)
        self.success_assertions(r)


    def test_sessions_version(self, tomcat, localwar_file, safe_path):
        r = tomcat.deploy_localwar(safe_path, localwar_file, version='42')
        self.success_assertions(r)

        r = tomcat.sessions(safe_path, version='42')
        self.info_assertions(r)
        assert r.result == r.sessions

        r = tomcat.undeploy(safe_path, version='42')
        self.success_assertions(r)

    ###
    #
    # expire
    #
    ###
    def test_expire_no_path(self, tomcat):
        with pytest.raises(ValueError):
            r = tomcat.expire(None)
        with pytest.raises(ValueError):
            r = tomcat.expire('')

    def test_expire(self, tomcat, localwar_file, safe_path):
        r = tomcat.deploy_localwar(safe_path, localwar_file)
        self.success_assertions(r)

        r = tomcat.expire(safe_path, idle=30)
        self.info_assertions(r)
        assert r.result == r.sessions

        r = tomcat.undeploy(safe_path)
        self.success_assertions(r)

    def test_expire_version(self, tomcat, localwar_file, safe_path):
        r = tomcat.deploy_localwar(safe_path, localwar_file, version='42')
        self.success_assertions(r)

        r = tomcat.expire(safe_path, version='42', idle=30)
        self.info_assertions(r)
        assert r.result == r.sessions

        r = tomcat.undeploy(safe_path, version='42')
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
        assert isinstance(r.apps[0], tm.models.TomcatApplication)
