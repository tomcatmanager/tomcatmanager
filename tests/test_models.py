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
# pylint: disable=protected-access, missing-function-docstring
# pylint: disable=missing-module-docstring, unused-variable, redefined-outer-name

from unittest import mock

import pytest
import requests

import tomcatmanager as tm

###
#
# test TomcatManagerResponse
#
###
def test_ok(tomcat):
    r = tomcat.list()
    assert r.ok


@pytest.fixture
def mock_text(mocker):
    return mocker.patch(
        "requests.models.Response.text", create=True, new_callable=mock.PropertyMock
    )


@pytest.mark.parametrize("value", [None, ""])
def test_http_response_empty(tomcat, mock_text, value):
    mock_text.return_value = value
    response = tomcat.vm_info()
    assert response.status_code is None
    assert response.status_message is None
    assert response.result is None


CONTENTS = [
    "malformedwithnospace",
    '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">',
]


@pytest.mark.parametrize("content", CONTENTS)
def test_http_response_not_tomcat(tomcat, mock_text, content):
    # like we might get if they put a regular web page in for the URL
    mock_text.return_value = content
    r = tomcat.vm_info()
    assert r.status_code == tm.StatusCode.NOTFOUND
    assert r.status_message == "Tomcat Manager not found"
    assert r.result is None


def test_http_status_server_error(tomcat, mocker):
    mock_code = mocker.patch(
        "requests.Response.status_code", create=True, new_callable=mock.PropertyMock
    )
    mock_code.return_value = requests.codes.server_error
    r = tomcat.vm_info()
    assert not r.ok


def test_http_result_valid(tomcat, mock_text):
    mock_text.return_value = "OK - some message\nthe result"
    r = tomcat.thread_dump()
    assert r.ok
    assert r.status_code == tm.StatusCode.OK
    assert r.status_message == "some message"
    assert r.result == "the result"


def test_http_result_fail(tomcat, mock_text):
    mock_text.return_value = "FAIL - some message"
    r = tomcat.thread_dump()
    assert not r.ok
    assert r.status_code == tm.StatusCode.FAIL
    assert r.status_message == "some message"
    assert r.result is None


###
#
# test ApplicationState
#
###
def test__application_state_parse_running():
    state = tm.ApplicationState.parse("running")
    assert state == tm.ApplicationState.RUNNING


def test_application_state_parse_stopped():
    state = tm.ApplicationState.parse("stopped")
    assert state == tm.ApplicationState.STOPPED


def test_application_state_parse_unknown():
    with pytest.raises(ValueError):
        _ = tm.ApplicationState.parse("fred flintstone")


###
#
# test TomcatApplication
#
###
@pytest.fixture
def apps():
    return """/:running:0:ROOT
/contacts:running:8:contacts##4.10
/shiny:stopped:17:shiny##v2.0.6
/contacts:running:5:contacts
/shiny:stopped:0:shiny##v2.0.5
/host-manager:stopped:0:/usr/share/tomcat8-admin/host-manager
/contacts:running:3:contacts##4.12
/shiny:running:12:shiny##v2.0.8
/manager:running:0:/usr/share/tomcat8-admin/manager
/shiny:running:15:shiny##v2.0.7
"""


def test_parse_root():
    line = "/:running:0:ROOT"
    tcapp = tm.models.TomcatApplication()
    tcapp.parse(line)
    assert tcapp.path == "/"
    assert tcapp.state == tm.ApplicationState.RUNNING
    assert tcapp.sessions == 0
    assert tcapp.directory == "ROOT"
    assert tcapp.version is None
    assert tcapp.directory_and_version == tcapp.directory


def test_parse_app_with_slash_in_directory():
    line = "/manager:running:0:/usr/share/tomcat8-admin/manager"
    tcapp = tm.models.TomcatApplication()
    tcapp.parse(line)
    assert tcapp.path == "/manager"
    assert tcapp.state == tm.ApplicationState.RUNNING
    assert tcapp.sessions == 0
    assert tcapp.directory == "/usr/share/tomcat8-admin/manager"
    assert tcapp.version is None
    assert tcapp.directory_and_version == tcapp.directory


def test_parse_app_with_non_integer_sessions():
    line = "/:running:not_an_integer:ROOT"
    tcapp = tm.models.TomcatApplication()
    with pytest.raises(ValueError):
        tcapp.parse(line)


def test_parse_version():
    line = "/shiny:stopped:17:shiny##v2.0.6"
    tcapp = tm.models.TomcatApplication()
    tcapp.parse(line)
    assert tcapp.path == "/shiny"
    assert tcapp.state == tm.ApplicationState.STOPPED
    assert tcapp.sessions == 17
    assert tcapp.directory == "shiny"
    assert tcapp.version == "v2.0.6"
    assert tcapp.directory_and_version == "shiny##v2.0.6"


def test_str_without_version():
    line = "/shiny:running:8:shiny"
    tcapp = tm.models.TomcatApplication()
    tcapp.parse(line)
    assert str(tcapp) == line


def test_str_with_version():
    line = "/shiny:stopped:17:shiny##v2.0.6"
    tcapp = tm.models.TomcatApplication()
    tcapp.parse(line)
    assert str(tcapp) == line


def test_str_with_zero_sessions():
    line = "/shiny:running:0:shiny##v2.0.6"
    tcapp = tm.models.TomcatApplication()
    tcapp.parse(line)
    assert str(tcapp) == line


def test_directory_and_version_empty():
    tcapp = tm.models.TomcatApplication()
    assert tcapp.directory_and_version is None


def parse_apps(lines):
    apps = []
    for line in lines.splitlines():
        app = tm.models.TomcatApplication()
        app.parse(line)
        apps.append(app)
    return apps


def test_lt(apps):
    sorted_apps = """/:running:0:ROOT
/contacts:running:5:contacts
/contacts:running:8:contacts##4.10
/contacts:running:3:contacts##4.12
/manager:running:0:/usr/share/tomcat8-admin/manager
/shiny:running:15:shiny##v2.0.7
/shiny:running:12:shiny##v2.0.8
/host-manager:stopped:0:/usr/share/tomcat8-admin/host-manager
/shiny:stopped:0:shiny##v2.0.5
/shiny:stopped:17:shiny##v2.0.6
"""
    apps = parse_apps(apps)
    apps.sort()
    result = ""
    strapps = map(str, apps)
    result = "\n".join(strapps) + "\n"
    assert result == sorted_apps


def test_sort_by_spv(apps):
    sorted_apps = """/:running:0:ROOT
/contacts:running:5:contacts
/contacts:running:8:contacts##4.10
/contacts:running:3:contacts##4.12
/manager:running:0:/usr/share/tomcat8-admin/manager
/shiny:running:15:shiny##v2.0.7
/shiny:running:12:shiny##v2.0.8
/host-manager:stopped:0:/usr/share/tomcat8-admin/host-manager
/shiny:stopped:0:shiny##v2.0.5
/shiny:stopped:17:shiny##v2.0.6
"""
    apps = parse_apps(apps)
    apps.sort(key=tm.models.TomcatApplication.sort_by_state_by_path_by_version)
    result = ""
    strapps = map(str, apps)
    result = "\n".join(strapps) + "\n"
    assert result == sorted_apps


def test_sort_by_pvs(apps):
    sorted_apps = """/:running:0:ROOT
/contacts:running:8:contacts##4.10
/contacts:running:3:contacts##4.12
/contacts:running:5:contacts
/host-manager:stopped:0:/usr/share/tomcat8-admin/host-manager
/manager:running:0:/usr/share/tomcat8-admin/manager
/shiny:stopped:0:shiny##v2.0.5
/shiny:stopped:17:shiny##v2.0.6
/shiny:running:15:shiny##v2.0.7
/shiny:running:12:shiny##v2.0.8
"""
    apps = parse_apps(apps)
    apps.sort(key=tm.models.TomcatApplication.sort_by_path_by_version_by_state)
    result = ""
    strapps = map(str, apps)
    result = "\n".join(strapps) + "\n"
    assert result == sorted_apps


###
#
# test ServerInfo
#
###
def test_dict(server_info):
    sinfo = tm.models.ServerInfo(result=server_info)
    assert sinfo["Tomcat Version"] == "Apache Tomcat/8.0.32 (Ubuntu)"
    assert sinfo["OS Name"] == "Linux"
    assert sinfo["OS Version"] == "4.4.0-89-generic"
    assert sinfo["OS Architecture"] == "amd64"
    assert sinfo["JVM Version"] == "1.8.0_131-8u131-b11-2ubuntu1.16.04.3-b11"
    assert sinfo["JVM Vendor"] == "Oracle Corporation"


def test_properties(server_info):
    sinfo = tm.models.ServerInfo(result=server_info)
    assert sinfo.tomcat_major_minor == tm.TomcatMajorMinor.V8_0
    assert sinfo.tomcat_version == "Apache Tomcat/8.0.32 (Ubuntu)"
    assert sinfo.os_name == "Linux"
    assert sinfo.os_version == "4.4.0-89-generic"
    assert sinfo.os_architecture == "amd64"
    assert sinfo.jvm_version == "1.8.0_131-8u131-b11-2ubuntu1.16.04.3-b11"
    assert sinfo.jvm_vendor == "Oracle Corporation"


def test_parse_extra(server_info):
    lines = server_info + "New Key: New Value\n"
    sinfo = tm.models.ServerInfo(result=lines)
    assert sinfo["New Key"] == "New Value"


###
#
# test TomcatMajor
#
###
TOMCAT_VERSIONS = [
    ("", tm.TomcatMajorMinor.UNSUPPORTED),
    ("Apache Tomcat/sixpointfive", tm.TomcatMajorMinor.UNSUPPORTED),
    ("Apache Tomcat/6.0.3", tm.TomcatMajorMinor.UNSUPPORTED),
    ("Tomcat Version: Apache Tomcat/7.0.33", tm.TomcatMajorMinor.UNSUPPORTED),
    ("Apache Tomcat/7.0.108", tm.TomcatMajorMinor.UNSUPPORTED),
    ("Apache Tomcat/8.0.0", tm.TomcatMajorMinor.V8_0),
    ("Apache Tomcat/8.5.16", tm.TomcatMajorMinor.V8_5),
    ("Apache Tomcat/9.0.44", tm.TomcatMajorMinor.V9_0),
    ("Tomcat Version: [Apache Tomcat/10.0.1", tm.TomcatMajorMinor.V10_0),
    ("[Apache Tomcat/10.0.4]", tm.TomcatMajorMinor.V10_0),
    ("[Apache Tomcat/10.1.3]", tm.TomcatMajorMinor.VNEXT),
    ("[Apache Tomcat/11.0.1]", tm.TomcatMajorMinor.VNEXT),
]


@pytest.mark.parametrize("version_string, major", TOMCAT_VERSIONS)
def test_tomcatmajor(version_string, major):
    assert tm.TomcatMajorMinor.parse(version_string) == major


def test_tomcatmajor_supported():
    assert tm.TomcatMajorMinor.supported() == [
        tm.TomcatMajorMinor.V8_0,
        tm.TomcatMajorMinor.V8_5,
        tm.TomcatMajorMinor.V9_0,
        tm.TomcatMajorMinor.V10_0,
    ]


def test_tomcatmajor_lowest():
    assert tm.TomcatMajorMinor.lowest_supported() == tm.TomcatMajorMinor.V8_0


def test_tomcatmajor_highest():
    assert tm.TomcatMajorMinor.highest_supported() == tm.TomcatMajorMinor.V10_0
