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

###
#
# deploy localwar
#
###
def test_deploy_localwar_path_only(tomcat, safe_path):
    with pytest.raises(ValueError):
        r = tomcat.deploy_localwar(safe_path, None)
    with pytest.raises(ValueError):
        r = tomcat.deploy_localwar(safe_path, '')

def test_deploy_localwar_warfile_only(tomcat, localwar_file):
    with pytest.raises(ValueError):
        r = tomcat.deploy_localwar(None, localwar_file)
    with pytest.raises(ValueError):
        r = tomcat.deploy_localwar('', localwar_file)

def test_deploy_localwar(tomcat, localwar_file, safe_path, assert_tomcatresponse):
    r = tomcat.deploy_localwar(safe_path, localwar_file)
    assert_tomcatresponse.success(r)
    assert_tomcatresponse.success(r)
    r = tomcat.undeploy(safe_path)
    assert_tomcatresponse.success(r)

def test_deploy_localwar_fileobj(tomcat, localwar_file, safe_path, assert_tomcatresponse):
    with open(localwar_file, 'rb') as localwar_fileobj:
        r = tomcat.deploy_localwar(safe_path, localwar_fileobj)
        assert_tomcatresponse.success(r)
    r = tomcat.undeploy(safe_path)
    assert_tomcatresponse.success(r)

def test_deploy_localwar_version(tomcat, localwar_file, safe_path, assert_tomcatresponse):
    r = tomcat.deploy_localwar(safe_path, localwar_file, version='42')
    assert_tomcatresponse.success(r)
    r = tomcat.undeploy(safe_path, version='42')
    assert_tomcatresponse.success(r)

def test_deploy_localwar_update(tomcat, localwar_file, safe_path, assert_tomcatresponse):
    r = tomcat.deploy_localwar(safe_path, localwar_file)
    assert_tomcatresponse.success(r)
    r = tomcat.deploy_localwar(safe_path, localwar_file, update=True)
    assert_tomcatresponse.success(r)
    r = tomcat.undeploy(safe_path)
    assert_tomcatresponse.success(r)

def test_deploy_localwar_version_update(tomcat, localwar_file, safe_path, assert_tomcatresponse):
    r = tomcat.deploy_localwar(safe_path, localwar_file, version='42')
    assert_tomcatresponse.success(r)
    r = tomcat.deploy_localwar(safe_path, localwar_file, version='42', update=True)
    assert_tomcatresponse.success(r)
    r = tomcat.undeploy(safe_path, version='42')
    assert_tomcatresponse.success(r)

###
#
# deploy serverwar
#
###
def test_deploy_serverwar_path_only(tomcat, safe_path):
    with pytest.raises(ValueError):
        r = tomcat.deploy_serverwar(safe_path, None)
    with pytest.raises(ValueError):
        r = tomcat.deploy_serverwar(safe_path, '')

def test_deploy_serverwar_warfile_only(tomcat, tomcat_manager_server):
    with pytest.raises(ValueError):
        r = tomcat.deploy_serverwar(None, tomcat_manager_server.warfile)
    with pytest.raises(ValueError):
        r = tomcat.deploy_serverwar('', tomcat_manager_server.warfile)

def test_deploy_serverwar(tomcat, tomcat_manager_server, safe_path, assert_tomcatresponse):
    r = tomcat.deploy_serverwar(safe_path, tomcat_manager_server.warfile)
    assert_tomcatresponse.success(r)
    r = tomcat.undeploy(safe_path)
    assert_tomcatresponse.success(r)

def test_deploy_serverwar_version(tomcat, tomcat_manager_server, safe_path, assert_tomcatresponse):
    r = tomcat.deploy_serverwar(safe_path, tomcat_manager_server.warfile, version='42')
    assert_tomcatresponse.success(r)
    r = tomcat.undeploy(safe_path, version='42')
    assert_tomcatresponse.success(r)

def test_deploy_serverwar_update(tomcat, tomcat_manager_server, safe_path, assert_tomcatresponse):
    r = tomcat.deploy_serverwar(safe_path, tomcat_manager_server.warfile)
    assert_tomcatresponse.success(r)
    r = tomcat.deploy_serverwar(safe_path, tomcat_manager_server.warfile, update=True)
    assert_tomcatresponse.success(r)
    r = tomcat.undeploy(safe_path)
    assert_tomcatresponse.success(r)

def test_deploy_serverwar_version_update(tomcat, tomcat_manager_server, safe_path, assert_tomcatresponse):
    r = tomcat.deploy_serverwar(safe_path, tomcat_manager_server.warfile, version='42')
    assert_tomcatresponse.success(r)
    r = tomcat.deploy_serverwar(safe_path, tomcat_manager_server.warfile, version='42', update=True)
    assert_tomcatresponse.success(r)
    r = tomcat.undeploy(safe_path, version='42')
    assert_tomcatresponse.success(r)

###
#
# deploy servercontext
#
###
def test_deploy_servercontext_path_only(tomcat, safe_path):
    with pytest.raises(ValueError):
        r = tomcat.deploy_servercontext(safe_path, None)
    with pytest.raises(ValueError):
        r = tomcat.deploy_servercontext(safe_path, '')

def test_deploy_servercontext_contextfile_only(tomcat, tomcat_manager_server):
    with pytest.raises(ValueError):
        r = tomcat.deploy_servercontext(None, tomcat_manager_server.contextfile)
    with pytest.raises(ValueError):
        r = tomcat.deploy_servercontext('', tomcat_manager_server.contextfile)

def test_deploy_servercontext_contextfile_and_war_only(tomcat, tomcat_manager_server):
    with pytest.raises(ValueError):
        r = tomcat.deploy_servercontext(
            None,
            tomcat_manager_server.contextfile,
            warfile=tomcat_manager_server.warfile
        )
    with pytest.raises(ValueError):
        r = tomcat.deploy_servercontext('', tomcat_manager_server.contextfile)

def test_deploy_servercontext(tomcat, tomcat_manager_server, safe_path, assert_tomcatresponse):
    r = tomcat.deploy_servercontext(safe_path, tomcat_manager_server.contextfile)
    assert_tomcatresponse.success(r)
    r = tomcat.undeploy(safe_path)
    assert_tomcatresponse.success(r)

def test_deploy_servercontext_update(tomcat, tomcat_manager_server, safe_path, assert_tomcatresponse):
    r = tomcat.deploy_servercontext(safe_path, tomcat_manager_server.contextfile)
    assert_tomcatresponse.success(r)
    r = tomcat.deploy_servercontext(safe_path, tomcat_manager_server.contextfile, update=True)
    assert_tomcatresponse.success(r)
    r = tomcat.undeploy(safe_path)
    assert_tomcatresponse.success(r)

def test_deploy_servercontext_version(tomcat, tomcat_manager_server, safe_path, assert_tomcatresponse):
    r = tomcat.deploy_servercontext(safe_path, tomcat_manager_server.contextfile, version='42')
    assert_tomcatresponse.success(r)
    r = tomcat.undeploy(safe_path, version='42')
    assert_tomcatresponse.success(r)

def test_deploy_servercontext_version_update(tomcat, tomcat_manager_server, safe_path, assert_tomcatresponse):
    r = tomcat.deploy_servercontext(safe_path, tomcat_manager_server.contextfile, version='42')
    assert_tomcatresponse.success(r)
    r = tomcat.deploy_servercontext(safe_path, tomcat_manager_server.contextfile, version='42', update=True)
    assert_tomcatresponse.success(r)
    r = tomcat.undeploy(safe_path, version='42')
    assert_tomcatresponse.success(r)

def test_deploy_servercontext_warfile(tomcat, tomcat_manager_server, safe_path, assert_tomcatresponse):
    r = tomcat.deploy_servercontext(safe_path, tomcat_manager_server.contextfile, tomcat_manager_server.warfile)
    assert_tomcatresponse.success(r)
    r = tomcat.undeploy(safe_path)
    assert_tomcatresponse.success(r)

def test_deploy_servercontext_warfile_update(tomcat, tomcat_manager_server, safe_path, assert_tomcatresponse):
    r = tomcat.deploy_servercontext(safe_path, tomcat_manager_server.contextfile, tomcat_manager_server.warfile)
    assert_tomcatresponse.success(r)
    r = tomcat.deploy_servercontext(safe_path, tomcat_manager_server.contextfile, tomcat_manager_server.warfile, update=True)
    assert_tomcatresponse.success(r)
    r = tomcat.undeploy(safe_path)
    assert_tomcatresponse.success(r)

def test_deploy_servercontext_warfile_version(tomcat, tomcat_manager_server, safe_path, assert_tomcatresponse):
    r = tomcat.deploy_servercontext(safe_path, tomcat_manager_server.contextfile, tomcat_manager_server.warfile, version='42')
    assert_tomcatresponse.success(r)
    r = tomcat.undeploy(safe_path, version='42')
    assert_tomcatresponse.success(r)

def test_deploy_servercontext_warfile_version_update(tomcat, tomcat_manager_server, safe_path, assert_tomcatresponse):
    r = tomcat.deploy_servercontext(safe_path, tomcat_manager_server.contextfile, tomcat_manager_server.warfile, version='42')
    assert_tomcatresponse.success(r)
    r = tomcat.deploy_servercontext(safe_path, tomcat_manager_server.contextfile, tomcat_manager_server.warfile, version='42', update=True)
    assert_tomcatresponse.success(r)
    r = tomcat.undeploy(safe_path, version='42')
    assert_tomcatresponse.success(r)

###
#
# undeploy
#
###
def test_undeploy_no_path(tomcat):
    with pytest.raises(ValueError):
        r = tomcat.undeploy(None)
    with pytest.raises(ValueError):
        r = tomcat.undeploy('')

###
#
# start and stop
#
###
def test_start_no_path(tomcat):
    with pytest.raises(ValueError):
        r = tomcat.start(None)
    with pytest.raises(ValueError):
        r = tomcat.start('')

def test_stop_no_path(tomcat):
    with pytest.raises(ValueError):
        r = tomcat.stop(None)
    with pytest.raises(ValueError):
        r = tomcat.stop('')

def test_stop_start(tomcat, localwar_file, safe_path, assert_tomcatresponse):
    with open(localwar_file, 'rb') as localwar_fileobj:
        r = tomcat.deploy_localwar(safe_path, localwar_fileobj)
    assert_tomcatresponse.success(r)

    r = tomcat.stop(safe_path)
    assert_tomcatresponse.success(r)

    r = tomcat.start(safe_path)
    assert_tomcatresponse.success(r)

    r = tomcat.undeploy(safe_path)
    assert_tomcatresponse.success(r)

def test_stop_start_version(tomcat, localwar_file, safe_path, assert_tomcatresponse):
    r = tomcat.deploy_localwar(safe_path, localwar_file, version='42')
    assert_tomcatresponse.success(r)

    r = tomcat.stop(safe_path, version='42')
    assert_tomcatresponse.success(r)

    r = tomcat.start(safe_path, version='42')
    assert_tomcatresponse.success(r)

    r = tomcat.undeploy(safe_path, version='42')
    assert_tomcatresponse.success(r)


###
#
# reload
#
###
def test_reload_no_path(tomcat):
    with pytest.raises(ValueError):
        r = tomcat.reload(None)
    with pytest.raises(ValueError):
        r = tomcat.reload('')

def test_reload(tomcat, localwar_file, safe_path, assert_tomcatresponse):
    r = tomcat.deploy_localwar(safe_path, localwar_file)
    assert_tomcatresponse.success(r)

    r = tomcat.reload(safe_path)
    assert_tomcatresponse.success(r)

    r = tomcat.undeploy(safe_path)
    assert_tomcatresponse.success(r)

def test_reload_version(tomcat, localwar_file, safe_path, assert_tomcatresponse):
    r = tomcat.deploy_localwar(safe_path, localwar_file, version='42')
    assert_tomcatresponse.success(r)

    r = tomcat.reload(safe_path, version='42')
    assert_tomcatresponse.success(r)

    r = tomcat.undeploy(safe_path, version='42')
    assert_tomcatresponse.success(r)


###
#
# sessions
#
###
def test_sessions_no_path(tomcat):
    with pytest.raises(ValueError):
        r = tomcat.sessions(None)
    with pytest.raises(ValueError):
        r = tomcat.sessions('')

def test_sessions(tomcat, localwar_file, safe_path, assert_tomcatresponse):
    r = tomcat.deploy_localwar(safe_path, localwar_file)
    assert_tomcatresponse.success(r)

    r = tomcat.sessions(safe_path)
    assert_tomcatresponse.info(r)
    assert r.result == r.sessions

    r = tomcat.undeploy(safe_path)
    assert_tomcatresponse.success(r)


def test_sessions_version(tomcat, localwar_file, safe_path, assert_tomcatresponse):
    r = tomcat.deploy_localwar(safe_path, localwar_file, version='42')
    assert_tomcatresponse.success(r)

    r = tomcat.sessions(safe_path, version='42')
    assert_tomcatresponse.info(r)
    assert r.result == r.sessions

    r = tomcat.undeploy(safe_path, version='42')
    assert_tomcatresponse.success(r)

###
#
# expire
#
###
def test_expire_no_path(tomcat):
    with pytest.raises(ValueError):
        r = tomcat.expire(None)
    with pytest.raises(ValueError):
        r = tomcat.expire('')

def test_expire(tomcat, localwar_file, safe_path, assert_tomcatresponse):
    r = tomcat.deploy_localwar(safe_path, localwar_file)
    assert_tomcatresponse.success(r)

    r = tomcat.expire(safe_path, idle=30)
    assert_tomcatresponse.info(r)
    assert r.result == r.sessions

    r = tomcat.undeploy(safe_path)
    assert_tomcatresponse.success(r)

def test_expire_version(tomcat, localwar_file, safe_path, assert_tomcatresponse):
    r = tomcat.deploy_localwar(safe_path, localwar_file, version='42')
    assert_tomcatresponse.success(r)

    r = tomcat.expire(safe_path, version='42', idle=30)
    assert_tomcatresponse.info(r)
    assert r.result == r.sessions

    r = tomcat.undeploy(safe_path, version='42')
    assert_tomcatresponse.success(r)

###
#
# list
#
###
def test_list(tomcat, assert_tomcatresponse):
    r = tomcat.list()
    assert_tomcatresponse.info(r)
    assert isinstance(r.apps, list)
    assert isinstance(r.apps[0], tm.models.TomcatApplication)
