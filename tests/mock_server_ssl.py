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
# pylint: disable=too-many-lines, too-many-public-methods

"""
Mock up a Tomcat Manager application that behaves like tomcat version 8.5+

This has all the SSL commands
"""

import re
import base64
from urllib.parse import urlparse
from urllib.parse import parse_qs
from http.server import BaseHTTPRequestHandler

import requests


def requires_authorization(func):
    """Decorator for methods which require authorization."""

    def _requires_authorization(self, *args, **kwargs):
        if self.authorized():
            func(self, *args, **kwargs)

    return _requires_authorization


class MockRequestHandlerSSL(BaseHTTPRequestHandler):
    """Handle HTTP Requests like Tomcat Manager 8.5+"""

    USER = "admin"
    PASSWORD = "admin"
    AUTH_KEY = base64.b64encode("{}:{}".format(USER, PASSWORD).encode("utf-8")).decode(
        "utf-8"
    )
    TEXT_PATTERN = re.compile(r"^/manager/text/?$")
    # info commands
    LIST_PATTERN = re.compile(r"^/manager/text/list($|\?.*$)")
    SERVER_INFO_PATTERN = re.compile(r"^/manager/text/serverinfo($|\?.*$)")
    STATUS_PATTERN = re.compile(r"^/manager/status(/|/all)?($|\?.*$)")
    VM_INFO_PATTERN = re.compile(r"^/manager/text/vminfo($|\?.*$)")
    SSL_CIPHERS_PATTERN = re.compile(r"^/manager/text/sslConnectorCiphers($|\?.*$)")
    SSL_CERTS_PATTERN = re.compile(r"^/manager/text/sslConnectorCerts($|\?.*$)")
    SSL_TRUSTED_CERTS_PATTERN = re.compile(
        r"^/manager/text/sslConnectorTrustedCerts($|\?.*$)"
    )
    SSL_RELOAD_PATTERN = re.compile(r"^/manager/text/sslReload($|\?.*$)")
    THREAD_DUMP_PATTERN = re.compile(r"^/manager/text/threaddump($|\?.*$)")
    RESOURCES_PATTERN = re.compile(r"^/manager/text/resources($|\?.*$)")
    FIND_LEAKERS_PATTERN = re.compile(r"^/manager/text/findleaks($|\?.*$)")
    SESSIONS_PATTERN = re.compile(r"^/manager/text/sessions($|\?.*$)")
    # action commands
    EXPIRE_PATTERN = re.compile(r"^/manager/text/expire($|\?.*$)")
    START_PATTERN = re.compile(r"^/manager/text/start($|\?.*$)")
    STOP_PATTERN = re.compile(r"^/manager/text/stop($|\?.*$)")
    RELOAD_PATTERN = re.compile(r"^/manager/text/reload($|\?.*$)")
    DEPLOY_PATTERN = re.compile(r"^/manager/text/deploy($|\?.*$)")
    UNDEPLOY_PATTERN = re.compile(r"^/manager/text/undeploy($|\?.*$)")

    def log_message(self, format_, *args):
        """no logging for our mockup"""
        # pylint: disable=arguments-differ,unused-argument
        return

    # pylint: disable=too-many-branches, invalid-name
    @requires_authorization
    def do_GET(self):
        """Handle all HTTP GET requests."""
        # handle request based on path
        if re.search(self.TEXT_PATTERN, self.path):
            self.send_fail("Unknown command")

        # the info commands
        elif re.search(self.LIST_PATTERN, self.path):
            self.get_list()
        elif re.search(self.SERVER_INFO_PATTERN, self.path):
            self.get_server_info()
        elif re.search(self.STATUS_PATTERN, self.path):
            self.get_status()
        elif re.search(self.VM_INFO_PATTERN, self.path):
            self.get_vm_info()
        elif re.search(self.SSL_CIPHERS_PATTERN, self.path):
            self.get_ssl_connector_ciphers()
        elif re.search(self.SSL_CERTS_PATTERN, self.path):
            self.get_ssl_connector_certs()
        elif re.search(self.SSL_TRUSTED_CERTS_PATTERN, self.path):
            self.get_ssl_connector_trusted_certs()
        elif re.search(self.SSL_RELOAD_PATTERN, self.path):
            self.get_ssl_reload()
        elif re.search(self.THREAD_DUMP_PATTERN, self.path):
            self.get_thread_dump()
        elif re.search(self.RESOURCES_PATTERN, self.path):
            self.get_resources()
        elif re.search(self.FIND_LEAKERS_PATTERN, self.path):
            self.get_find_leakers()
        elif re.search(self.SESSIONS_PATTERN, self.path):
            self.get_sessions()

        # the action commands
        elif re.search(self.EXPIRE_PATTERN, self.path):
            self.get_expire()
        elif re.search(self.START_PATTERN, self.path):
            self.get_start()
        elif re.search(self.STOP_PATTERN, self.path):
            self.get_stop()
        elif re.search(self.RELOAD_PATTERN, self.path):
            self.get_reload()
        elif re.search(self.DEPLOY_PATTERN, self.path):
            self.get_deploy()
        elif re.search(self.UNDEPLOY_PATTERN, self.path):
            self.get_undeploy()

        # fail if we don't recognize the path
        else:
            self.send_fail("Unknown command")

    @requires_authorization
    def do_PUT(self):
        """Handle all HTTP PUT requests."""
        if re.search(self.DEPLOY_PATTERN, self.path):
            self.put_deploy()
        else:
            self.send_fail("Unknown command")

    ###
    #
    # convenience methods
    #
    ###
    def authorized(self):
        """Check authorization and return True or False."""
        # first check authentication
        if self.headers.get("Authorization") == "Basic " + self.AUTH_KEY:
            return True

        # pylint: disable=no-member
        self.send_response(requests.codes.unauthorized)
        self.send_header("WWW-Authenticate", 'Basic realm="tomcatmanager"')
        self.send_header("Content-type", "text/html")
        self.end_headers()
        msg = "not authorized"
        self.wfile.write(msg.encode("utf-8"))
        return False

    def ensure_path(self, failmsg):
        """Ensure we have a path in the query string.

        Return the path if the path parameter is present. The Tomcat Manager web app
        seems to assume of the path parameter is present, but the supplied path is an
        empty string, the path to use is '/', so that's what we return here

        If no path is present return None and send the fail message.
        """
        url = urlparse(self.path)
        query_string = parse_qs(url.query, keep_blank_values=True)
        path = None
        if "path" in query_string:
            path = query_string["path"]
            if path == "":
                path = "/"
        else:
            self.send_fail(failmsg)
        return path

    def send_fail(self, msg=None):
        """Send the Tomcat FAIL message."""
        self.send_text("FAIL - {}".format(msg))

    def send_text(self, content):
        """Send a status ok and content as text/html."""
        # pylint: disable=no-member
        self.send_response(requests.codes.ok)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    ###
    #
    # the info commands, i.e. commands that don't really do anything, they
    # just return some information from the server
    #
    ###
    def get_list(self):
        """Send a list of applications."""
        self.send_text(
            """OK - Listed applications for virtual host localhost
/:running:0:ROOT
/contacts:running:3:running##4.1
/shiny:stopped:17:shiny##v2.0.6
/contacts:running:8:running
/shiny:stopped:0:shiny##v2.0.5
/host-manager:stopped:0:/usr/share/tomcat8-admin/host-manager
/shiny:running:12:shiny##v2.0.8
/manager:running:0:/usr/share/tomcat8-admin/manager
/shiny:running:15:shiny##v2.0.7
"""
        )

    def get_server_info(self):
        """Send the server information."""
        self.send_text(
            """OK - Server info
Tomcat Version: [Apache Tomcat/8.5.65]
OS Name: [Linux]
OS Version: [5.4.0-67-generic]
OS Architecture: [amd64]
JVM Version: [1.8.0_282-8u282-b08-0ubuntu1~20.04-b08]
JVM Vendor: [Private Build]"""
        )

    # pylint: disable=line-too-long
    def get_status(self):
        """Send the status XML."""
        self.send_text(
            """<?xml version="1.0" encoding="utf-8"?><?xml-stylesheet type="text/xsl" href="/manager/xform.xsl" ?>
<status><jvm><memory free='22294576' total='36569088' max='129761280'/><memorypool name='CMS Old Gen' type='Heap memory' usageInit='22413312' usageCommitted='25165824' usageMax='89522176' usageUsed='13503656'/><memorypool name='Par Eden Space' type='Heap memory' usageInit='8912896' usageCommitted='10158080' usageMax='35782656' usageUsed='299600'/><memorypool name='Par Survivor Space' type='Heap memory' usageInit='1114112' usageCommitted='1245184' usageMax='4456448' usageUsed='473632'/><memorypool name='Code Cache' type='Non-heap memory' usageInit='2555904' usageCommitted='12713984' usageMax='251658240' usageUsed='12510656'/><memorypool name='Compressed Class Space' type='Non-heap memory' usageInit='0' usageCommitted='2621440' usageMax='1073741824' usageUsed='2400424'/><memorypool name='Metaspace' type='Non-heap memory' usageInit='0' usageCommitted='24903680' usageMax='-1' usageUsed='24230432'/></jvm><connector name='"http-nio-8080"'><threadInfo  maxThreads="200" currentThreadCount="10" currentThreadsBusy="1" /><requestInfo  maxTime="570" processingTime="2015" requestCount="868" errorCount="494" bytesReceived="0" bytesSent="1761440" /><workers><worker  stage="S" requestProcessingTime="1" requestBytesSent="0" requestBytesReceived="0" remoteAddr="192.168.13.22" virtualHost="192.168.13.66" method="GET" currentUri="/manager/status/all" currentQueryString="XML=true" protocol="HTTP/1.1" /><worker  stage="R" requestProcessingTime="0" requestBytesSent="0" requestBytesReceived="0" remoteAddr="&#63;" virtualHost="&#63;" method="&#63;" currentUri="&#63;" currentQueryString="&#63;" protocol="&#63;" /></workers></connector></status>
        """
        )

    def get_vm_info(self):
        """Send the jvm info."""
        self.send_text(
            """OK - VM info
2017-08-07 00:55:24.199
Runtime information:
  vmName: OpenJDK 64-Bit Server VM
  vmVersion: 25.131-b11
  vmVendor: Oracle Corporation
  specName: Java Virtual Machine Specification
  specVersion: 1.8
  specVendor: Oracle Corporation
  managementSpecVersion: 1.2
  name: 6403@tomcat
  startTime: 1501951074623
  uptime: 124960918
  isBootClassPathSupported: true

OS information:
  name: Linux
  version: 4.4.0-89-generic
  architecture: amd64
  availableProcessors: 2
  systemLoadAverage: 0.0

ThreadMXBean capabilities:
  isCurrentThreadCpuTimeSupported: true
  isThreadCpuTimeSupported: true
  isThreadCpuTimeEnabled: true
  isObjectMonitorUsageSupported: true
  isSynchronizerUsageSupported: true
  isThreadContentionMonitoringSupported: true
  isThreadContentionMonitoringEnabled: false

Thread counts:
  daemon: 19
  total: 20
  peak: 20
  totalStarted: 22

Startup arguments:
  -Djava.util.logging.config.file=/var/lib/tomcat8/conf/logging.properties
  -Djava.util.logging.manager=org.apache.juli.ClassLoaderLogManager
  -Djava.awt.headless=true
  -Xmx128m
  -XX:+UseConcMarkSweepGC
  -Djava.endorsed.dirs=/usr/share/tomcat8/endorsed
  -Dcatalina.base=/var/lib/tomcat8
  -Dcatalina.home=/usr/share/tomcat8
  -Djava.io.tmpdir=/tmp/tomcat8-tomcat8-tmp

Path information:
  bootClassPath: /usr/lib/jvm/java-8-openjdk-amd64/jre/lib/resources.jar:/usr/lib/jvm/java-8-openjdk-amd64/jre/lib/rt.jar:/usr/lib/jvm/java-8-openjdk-amd64/jre/lib/sunrsasign.jar:/usr/lib/jvm/java-8-openjdk-amd64/jre/lib/jsse.jar:/usr/lib/jvm/java-8-openjdk-amd64/jre/lib/jce.jar:/usr/lib/jvm/java-8-openjdk-amd64/jre/lib/charsets.jar:/usr/lib/jvm/java-8-openjdk-amd64/jre/lib/jfr.jar:/usr/lib/jvm/java-8-openjdk-amd64/jre/classes
  classPath: /usr/share/tomcat8/bin/bootstrap.jar:/usr/share/tomcat8/bin/tomcat-juli.jar
  libraryPath: /usr/java/packages/lib/amd64:/usr/lib/x86_64-linux-gnu/jni:/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:/usr/lib/jni:/lib:/usr/lib

Class loading:
  loaded: 3357
  unloaded: 5
  totalLoaded: 3362
  isVerbose: false

Class compilation:
  name: HotSpot 64-Bit Tiered Compilers
  totalCompilationTime: 8462
  isCompilationTimeMonitoringSupported: true

Memory Manager [CodeCacheManager]:
  isValid: true
  mbean.getMemoryPoolNames:
    Code Cache

Memory Manager [Metaspace Manager]:
  isValid: true
  mbean.getMemoryPoolNames:
    Compressed Class Space
    Metaspace

Memory Manager [ParNew]:
  isValid: true
  mbean.getMemoryPoolNames:
    Par Eden Space
    Par Survivor Space

Memory Manager [ConcurrentMarkSweep]:
  isValid: true
  mbean.getMemoryPoolNames:
    CMS Old Gen
    Par Eden Space
    Par Survivor Space

Garbage Collector [ParNew]:
  isValid: true
  mbean.getMemoryPoolNames:
    Par Eden Space
    Par Survivor Space
  getCollectionCount: 61
  getCollectionTime: 161

Garbage Collector [ConcurrentMarkSweep]:
  isValid: true
  mbean.getMemoryPoolNames:
    CMS Old Gen
    Par Eden Space
    Par Survivor Space
  getCollectionCount: 17
  getCollectionTime: 203

Memory information:
  isVerbose: false
  getObjectPendingFinalizationCount: 0
  heap init: 33554432
  heap used: 15019296
  heap committed: 36569088
  heap max: 129761280
  non-heap init: 2555904
  non-heap used: 39402128
  non-heap committed: 40370176
  non-heap max: -1

Memory Pool [Code Cache]:
  isValid: true
  getType: Non-heap memory
  mbean.getMemoryManagerNames:
    CodeCacheManager
  isUsageThresholdSupported: true
  isUsageThresholdExceeded: false
  isCollectionUsageThresholdSupported: false
  getUsageThreshold: 0
  getUsageThresholdCount: 0
  current init: 2555904
  current used: 12715968
  current committed: 12845056
  current max: 251658240
  peak init: 2555904
  peak used: 12715968
  peak committed: 12845056
  peak max: 251658240

Memory Pool [Metaspace]:
  isValid: true
  getType: Non-heap memory
  mbean.getMemoryManagerNames:
    Metaspace Manager
  isUsageThresholdSupported: true
  isUsageThresholdExceeded: false
  isCollectionUsageThresholdSupported: false
  getUsageThreshold: 0
  getUsageThresholdCount: 0
  current init: 0
  current used: 24281872
  current committed: 24903680
  current max: -1
  peak init: 0
  peak used: 24281872
  peak committed: 24903680
  peak max: -1

Memory Pool [Compressed Class Space]:
  isValid: true
  getType: Non-heap memory
  mbean.getMemoryManagerNames:
    Metaspace Manager
  isUsageThresholdSupported: true
  isUsageThresholdExceeded: false
  isCollectionUsageThresholdSupported: false
  getUsageThreshold: 0
  getUsageThresholdCount: 0
  current init: 0
  current used: 2404288
  current committed: 2621440
  current max: 1073741824
  peak init: 0
  peak used: 2404288
  peak committed: 2621440
  peak max: 1073741824

Memory Pool [Par Eden Space]:
  isValid: true
  getType: Heap memory
  mbean.getMemoryManagerNames:
    ConcurrentMarkSweep
    ParNew
  isUsageThresholdSupported: false
  isCollectionUsageThresholdSupported: true
  isCollectionUsageThresholdExceeded: false
  getCollectionUsageThreshold: 0
  getCollectionUsageThresholdCount: 0
  current init: 8912896
  current used: 1127152
  current committed: 10158080
  current max: 35782656
  collection init: 8912896
  collection used: 0
  collection committed: 10158080
  collection max: 35782656
  peak init: 8912896
  peak used: 10158080
  peak committed: 10158080
  peak max: 35782656

Memory Pool [Par Survivor Space]:
  isValid: true
  getType: Heap memory
  mbean.getMemoryManagerNames:
    ConcurrentMarkSweep
    ParNew
  isUsageThresholdSupported: false
  isCollectionUsageThresholdSupported: true
  isCollectionUsageThresholdExceeded: false
  getCollectionUsageThreshold: 0
  getCollectionUsageThresholdCount: 0
  current init: 1114112
  current used: 160608
  current committed: 1245184
  current max: 4456448
  collection init: 1114112
  collection used: 160608
  collection committed: 1245184
  collection max: 4456448
  peak init: 1114112
  peak used: 1114112
  peak committed: 1245184
  peak max: 4456448

Memory Pool [CMS Old Gen]:
  isValid: true
  getType: Heap memory
  mbean.getMemoryManagerNames:
    ConcurrentMarkSweep
  isUsageThresholdSupported: true
  isUsageThresholdExceeded: false
  isCollectionUsageThresholdSupported: true
  isCollectionUsageThresholdExceeded: false
  getUsageThreshold: 0
  getUsageThresholdCount: 0
  getCollectionUsageThreshold: 0
  getCollectionUsageThresholdCount: 0
  current init: 22413312
  current used: 13787424
  current committed: 25165824
  current max: 89522176
  collection init: 22413312
  collection used: 13176808
  collection committed: 25165824
  collection max: 89522176
  peak init: 22413312
  peak used: 24748376
  peak committed: 25165824
  peak max: 89522176

System properties:
  awt.toolkit: sun.awt.X11.XToolkit
  catalina.base: /var/lib/tomcat8
  catalina.home: /usr/share/tomcat8
  catalina.useNaming: true
  common.loader: "${catalina.base}/lib","${catalina.base}/lib/*.jar","${catalina.home}/lib","${catalina.home}/lib/*.jar","${catalina.home}/common/classes","${catalina.home}/common/*.jar"
  file.encoding: UTF-8
  file.encoding.pkg: sun.io
  file.separator: /
  java.awt.graphicsenv: sun.awt.X11GraphicsEnvironment
  java.awt.headless: true
  java.awt.printerjob: sun.print.PSPrinterJob
  java.class.path: /usr/share/tomcat8/bin/bootstrap.jar:/usr/share/tomcat8/bin/tomcat-juli.jar
  java.class.version: 52.0
  java.endorsed.dirs: /usr/share/tomcat8/endorsed
  java.ext.dirs: /usr/lib/jvm/java-8-openjdk-amd64/jre/lib/ext:/usr/java/packages/lib/ext
  java.home: /usr/lib/jvm/java-8-openjdk-amd64/jre
  java.io.tmpdir: /tmp/tomcat8-tomcat8-tmp
  java.library.path: /usr/java/packages/lib/amd64:/usr/lib/x86_64-linux-gnu/jni:/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:/usr/lib/jni:/lib:/usr/lib
  java.naming.factory.initial: org.apache.naming.java.javaURLContextFactory
  java.naming.factory.url.pkgs: org.apache.naming
  java.runtime.name: OpenJDK Runtime Environment
  java.runtime.version: 1.8.0_131-8u131-b11-2ubuntu1.16.04.3-b11
  java.specification.name: Java Platform API Specification
  java.specification.vendor: Oracle Corporation
  java.specification.version: 1.8
  java.util.logging.config.file: /var/lib/tomcat8/conf/logging.properties
  java.util.logging.manager: org.apache.juli.ClassLoaderLogManager
  java.vendor: Oracle Corporation
  java.vendor.url: http://java.oracle.com/
  java.vendor.url.bug: http://bugreport.sun.com/bugreport/
  java.version: 1.8.0_131
  java.vm.info: mixed mode
  java.vm.name: OpenJDK 64-Bit Server VM
  java.vm.specification.name: Java Virtual Machine Specification
  java.vm.specification.vendor: Oracle Corporation
  java.vm.specification.version: 1.8
  java.vm.vendor: Oracle Corporation
  java.vm.version: 25.131-b11
  line.separator:

  os.arch: amd64
  os.name: Linux
  os.version: 4.4.0-89-generic
  package.access: sun.,org.apache.catalina.,org.apache.coyote.,org.apache.jasper.,org.apache.tomcat.
  package.definition: sun.,java.,org.apache.catalina.,org.apache.coyote.,org.apache.jasper.,org.apache.naming.,org.apache.tomcat.
  path.separator: :
  server.loader: ${catalina.home}/server/classes,${catalina.home}/server/*.jar
  shared.loader: ${catalina.home}/shared/classes,${catalina.home}/shared/*.jar
  sun.arch.data.model: 64
  sun.boot.class.path: /usr/lib/jvm/java-8-openjdk-amd64/jre/lib/resources.jar:/usr/lib/jvm/java-8-openjdk-amd64/jre/lib/rt.jar:/usr/lib/jvm/java-8-openjdk-amd64/jre/lib/sunrsasign.jar:/usr/lib/jvm/java-8-openjdk-amd64/jre/lib/jsse.jar:/usr/lib/jvm/java-8-openjdk-amd64/jre/lib/jce.jar:/usr/lib/jvm/java-8-openjdk-amd64/jre/lib/charsets.jar:/usr/lib/jvm/java-8-openjdk-amd64/jre/lib/jfr.jar:/usr/lib/jvm/java-8-openjdk-amd64/jre/classes
  sun.boot.library.path: /usr/lib/jvm/java-8-openjdk-amd64/jre/lib/amd64
  sun.cpu.endian: little
  sun.cpu.isalist:
  sun.io.unicode.encoding: UnicodeLittle
  sun.java.command: org.apache.catalina.startup.Bootstrap start
  sun.java.launcher: SUN_STANDARD
  sun.jnu.encoding: UTF-8
  sun.management.compiler: HotSpot 64-Bit Tiered Compilers
  sun.os.patch.level: unknown
  tomcat.util.buf.StringCache.byte.enabled: true
  tomcat.util.scan.StandardJarScanFilter.jarsToScan: log4j-core*.jar,log4j-taglib*.jar,log4javascript*.jar
  tomcat.util.scan.StandardJarScanFilter.jarsToSkip: bootstrap.jar,commons-daemon.jar,tomcat-juli.jar,annotations-api.jar,el-api.jar,jsp-api.jar,servlet-api.jar,websocket-api.jar,catalina.jar,catalina-ant.jar,catalina-ha.jar,catalina-storeconfig.jar,catalina-tribes.jar,jasper.jar,jasper-el.jar,ecj-*.jar,tomcat-api.jar,tomcat-util.jar,tomcat-util-scan.jar,tomcat-coyote.jar,tomcat-dbcp.jar,tomcat-jni.jar,tomcat-websocket.jar,tomcat-i18n-en.jar,tomcat-i18n-es.jar,tomcat-i18n-fr.jar,tomcat-i18n-ja.jar,tomcat-juli-adapters.jar,catalina-jmx-remote.jar,catalina-ws.jar,tomcat-jdbc.jar,tools.jar,commons-beanutils*.jar,commons-codec*.jar,commons-collections*.jar,commons-dbcp*.jar,commons-digester*.jar,commons-fileupload*.jar,commons-httpclient*.jar,commons-io*.jar,commons-lang*.jar,commons-logging*.jar,commons-math*.jar,commons-pool*.jar,jstl.jar,taglibs-standard-spec-*.jar,geronimo-spec-jaxrpc*.jar,wsdl4j*.jar,ant.jar,ant-junit*.jar,aspectj*.jar,jmx.jar,h2*.jar,hibernate*.jar,httpclient*.jar,jmx-tools.jar,jta*.jar,log4j*.jar,mail*.jar,slf4j*.jar,xercesImpl.jar,xmlParserAPIs.jar,xml-apis.jar,junit.jar,junit-*.jar,ant-launcher.jar,cobertura-*.jar,asm-*.jar,dom4j-*.jar,icu4j-*.jar,jaxen-*.jar,jdom-*.jar,jetty-*.jar,oro-*.jar,servlet-api-*.jar,tagsoup-*.jar,xmlParserAPIs-*.jar,xom-*.jar
  user.country: US
  user.dir: /var/lib/tomcat8
  user.home: /usr/share/tomcat8
  user.language: en
  user.name: tomcat8
  user.timezone: America/Denver

Logger information:
  : level=, parent=
  org: level=, parent=
  org.apache: level=, parent=org
  org.apache.catalina: level=, parent=org.apache
  org.apache.catalina.core: level=, parent=org.apache.catalina
  org.apache.catalina.core.ContainerBase: level=, parent=org.apache.catalina.core
  org.apache.catalina.core.ContainerBase.[Catalina]: level=, parent=org.apache.catalina.core.ContainerBase
  org.apache.catalina.core.ContainerBase.[Catalina].[localhost]: level=INFO, parent=org.apache.catalina.core.ContainerBase.[Catalina]
  org.apache.catalina.core.ContainerBase.[Catalina].[localhost].[/manager]: level=, parent=org.apache.catalina.core.ContainerBase.[Catalina].[localhost]
  org.apache.catalina.core.ContainerBase.[Catalina].[localhost].[/manager].[HTMLManager]: level=, parent=org.apache.catalina.core.ContainerBase.[Catalina].[localhost].[/manager]
  org.apache.catalina.core.ContainerBase.[Catalina].[localhost].[/manager].[JMXProxy]: level=, parent=org.apache.catalina.core.ContainerBase.[Catalina].[localhost].[/manager]
  org.apache.catalina.core.ContainerBase.[Catalina].[localhost].[/manager].[Manager]: level=, parent=org.apache.catalina.core.ContainerBase.[Catalina].[localhost].[/manager]
  org.apache.catalina.core.ContainerBase.[Catalina].[localhost].[/manager].[Status]: level=, parent=org.apache.catalina.core.ContainerBase.[Catalina].[localhost].[/manager]
  org.apache.catalina.core.ContainerBase.[Catalina].[localhost].[/manager].[default]: level=, parent=org.apache.catalina.core.ContainerBase.[Catalina].[localhost].[/manager]
  org.apache.catalina.core.ContainerBase.[Catalina].[localhost].[/manager].[jsp]: level=, parent=org.apache.catalina.core.ContainerBase.[Catalina].[localhost].[/manager]
  org.apache.catalina.session: level=, parent=org.apache.catalina
  org.apache.catalina.session.ManagerBase: level=, parent=org.apache.catalina.session
  org.apache.catalina.session.StandardManager: level=, parent=org.apache.catalina.session
  org.apache.catalina.util: level=, parent=org.apache.catalina
  org.apache.catalina.util.RequestUtil: level=, parent=org.apache.catalina.util
  org.apache.jasper: level=, parent=org.apache
  org.apache.jasper.EmbeddedServletOptions: level=, parent=org.apache.jasper
  org.apache.jasper.JspCompilationContext: level=, parent=org.apache.jasper
  org.apache.jasper.compiler: level=, parent=org.apache.jasper
  org.apache.jasper.compiler.Compiler: level=, parent=org.apache.jasper.compiler
  org.apache.jasper.compiler.JDTCompiler: level=, parent=org.apache.jasper.compiler
  org.apache.jasper.compiler.JspConfig: level=, parent=org.apache.jasper.compiler
  org.apache.jasper.compiler.JspReader: level=, parent=org.apache.jasper.compiler
  org.apache.jasper.compiler.JspRuntimeContext: level=, parent=org.apache.jasper.compiler
  org.apache.jasper.compiler.SmapUtil$SDEInstaller: level=, parent=org.apache.jasper.compiler
  org.apache.jasper.servlet: level=, parent=org.apache.jasper
  org.apache.jasper.servlet.JspServlet: level=, parent=org.apache.jasper.servlet
  org.apache.jasper.servlet.JspServletWrapper: level=, parent=org.apache.jasper.servlet
  org.apache.jasper.xmlparser: level=, parent=org.apache.jasper
  org.apache.jasper.xmlparser.UTF8Reader: level=, parent=org.apache.jasper.xmlparser
  org.apache.tomcat: level=, parent=org.apache
  org.apache.tomcat.util: level=, parent=org.apache.tomcat
  org.apache.tomcat.util.Diagnostics: level=, parent=org.apache.tomcat.util
  org.apache.tomcat.util.digester: level=, parent=org.apache.tomcat.util
  org.apache.tomcat.util.digester.Digester: level=, parent=org.apache.tomcat.util.digester
  org.apache.tomcat.util.digester.Digester.sax: level=, parent=org.apache.tomcat.util.digester.Digester
  org.apache.tomcat.websocket: level=, parent=org.apache.tomcat
  org.apache.tomcat.websocket.WsWebSocketContainer: level=, parent=org.apache.tomcat.websocket
"""
        )

    def get_ssl_connector_ciphers(self):
        """Send the SSL ciphers."""
        self.send_text(
            """OK - Connector / SSL Cipher information
Connector[HTTP/1.1-8080]
  SSL is not enabled for this connector"""
        )

    def get_ssl_connector_certs(self):
        """Send the SSL certs."""
        self.send_text(
            """OK - Connector / Certificate Chain information
Connector[HTTP/1.1-8080]
SSL is not enabled for this connector"""
        )

    def get_ssl_connector_trusted_certs(self):
        """Send the trusted SSL certs."""
        self.send_text(
            """OK - Connector / Trusted Certificate information
Connector[HTTP/1.1-8080]
SSL is not enabled for this connector"""
        )

    def get_ssl_reload(self):
        """Reload the SSL certificates."""
        url = urlparse(self.path)
        query_string = parse_qs(url.query, keep_blank_values=True)
        host_name = None
        if "tlsHostName" in query_string:
            host_name = query_string["tlsHostName"]
            self.send_text("OK - Reloaded TLS configuration for [{}]".format(host_name))
        else:
            self.send_text("""OK - Reloaded TLS configuration for [_default_]""")

    def get_thread_dump(self):
        """Send a JVM thread dump"""
        self.send_text(
            """OK - JVM thread dump
2017-08-07 11:00:20.517
Full thread dump OpenJDK 64-Bit Server VM (25.131-b11 mixed mode):

"http-nio-8080-exec-10" Id=29 cpu=138306254 ns usr=90000000 ns blocked 0 for -1 ms waited 89 for -1 ms
   java.lang.Thread.State: WAITING
    at sun.misc.Unsafe.park(Native Method)
    - waiting on (a java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject@337a3b83)
    at java.util.concurrent.locks.LockSupport.park(LockSupport.java:175)
    at java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject.await(AbstractQueuedSynchronizer.java:2039)
    at java.util.concurrent.LinkedBlockingQueue.take(LinkedBlockingQueue.java:442)
    at org.apache.tomcat.util.threads.TaskQueue.take(TaskQueue.java:103)
    at org.apache.tomcat.util.threads.TaskQueue.take(TaskQueue.java:31)
    at java.util.concurrent.ThreadPoolExecutor.getTask(ThreadPoolExecutor.java:1074)
    at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1134)
    at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
    at org.apache.tomcat.util.threads.TaskThread$WrappingRunnable.run(TaskThread.java:61)
    at java.lang.Thread.run(Thread.java:748)

"http-nio-8080-exec-9" Id=28 cpu=187396179 ns usr=140000000 ns blocked 1 for -1 ms waited 89 for -1 ms
   java.lang.Thread.State: WAITING
    at sun.misc.Unsafe.park(Native Method)
    - waiting on (a java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject@337a3b83)
    at java.util.concurrent.locks.LockSupport.park(LockSupport.java:175)
    at java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject.await(AbstractQueuedSynchronizer.java:2039)
    at java.util.concurrent.LinkedBlockingQueue.take(LinkedBlockingQueue.java:442)
    at org.apache.tomcat.util.threads.TaskQueue.take(TaskQueue.java:103)
    at org.apache.tomcat.util.threads.TaskQueue.take(TaskQueue.java:31)
    at java.util.concurrent.ThreadPoolExecutor.getTask(ThreadPoolExecutor.java:1074)
    at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1134)
    at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
    at org.apache.tomcat.util.threads.TaskThread$WrappingRunnable.run(TaskThread.java:61)
    at java.lang.Thread.run(Thread.java:748)

"http-nio-8080-exec-8" Id=27 cpu=133198544 ns usr=100000000 ns blocked 1 for -1 ms waited 89 for -1 ms
   java.lang.Thread.State: WAITING
    at sun.misc.Unsafe.park(Native Method)
    - waiting on (a java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject@337a3b83)
    at java.util.concurrent.locks.LockSupport.park(LockSupport.java:175)
    at java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject.await(AbstractQueuedSynchronizer.java:2039)
    at java.util.concurrent.LinkedBlockingQueue.take(LinkedBlockingQueue.java:442)
    at org.apache.tomcat.util.threads.TaskQueue.take(TaskQueue.java:103)
    at org.apache.tomcat.util.threads.TaskQueue.take(TaskQueue.java:31)
    at java.util.concurrent.ThreadPoolExecutor.getTask(ThreadPoolExecutor.java:1074)
    at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1134)
    at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
    at org.apache.tomcat.util.threads.TaskThread$WrappingRunnable.run(TaskThread.java:61)
    at java.lang.Thread.run(Thread.java:748)

"http-nio-8080-exec-7" Id=26 cpu=131936317 ns usr=100000000 ns blocked 0 for -1 ms waited 89 for -1 ms
   java.lang.Thread.State: WAITING
    at sun.misc.Unsafe.park(Native Method)
    - waiting on (a java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject@337a3b83)
    at java.util.concurrent.locks.LockSupport.park(LockSupport.java:175)
    at java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject.await(AbstractQueuedSynchronizer.java:2039)
    at java.util.concurrent.LinkedBlockingQueue.take(LinkedBlockingQueue.java:442)
    at org.apache.tomcat.util.threads.TaskQueue.take(TaskQueue.java:103)
    at org.apache.tomcat.util.threads.TaskQueue.take(TaskQueue.java:31)
    at java.util.concurrent.ThreadPoolExecutor.getTask(ThreadPoolExecutor.java:1074)
    at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1134)
    at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
    at org.apache.tomcat.util.threads.TaskThread$WrappingRunnable.run(TaskThread.java:61)
    at java.lang.Thread.run(Thread.java:748)

"http-nio-8080-exec-6" Id=25 cpu=143839244 ns usr=110000000 ns blocked 0 for -1 ms waited 89 for -1 ms
   java.lang.Thread.State: WAITING
    at sun.misc.Unsafe.park(Native Method)
    - waiting on (a java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject@337a3b83)
    at java.util.concurrent.locks.LockSupport.park(LockSupport.java:175)
    at java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject.await(AbstractQueuedSynchronizer.java:2039)
    at java.util.concurrent.LinkedBlockingQueue.take(LinkedBlockingQueue.java:442)
    at org.apache.tomcat.util.threads.TaskQueue.take(TaskQueue.java:103)
    at org.apache.tomcat.util.threads.TaskQueue.take(TaskQueue.java:31)
    at java.util.concurrent.ThreadPoolExecutor.getTask(ThreadPoolExecutor.java:1074)
    at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1134)
    at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
    at org.apache.tomcat.util.threads.TaskThread$WrappingRunnable.run(TaskThread.java:61)
    at java.lang.Thread.run(Thread.java:748)

"http-nio-8080-exec-5" Id=24 cpu=128710627 ns usr=90000000 ns blocked 0 for -1 ms waited 89 for -1 ms
   java.lang.Thread.State: WAITING
    at sun.misc.Unsafe.park(Native Method)
    - waiting on (a java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject@337a3b83)
    at java.util.concurrent.locks.LockSupport.park(LockSupport.java:175)
    at java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject.await(AbstractQueuedSynchronizer.java:2039)
    at java.util.concurrent.LinkedBlockingQueue.take(LinkedBlockingQueue.java:442)
    at org.apache.tomcat.util.threads.TaskQueue.take(TaskQueue.java:103)
    at org.apache.tomcat.util.threads.TaskQueue.take(TaskQueue.java:31)
    at java.util.concurrent.ThreadPoolExecutor.getTask(ThreadPoolExecutor.java:1074)
    at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1134)
    at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
    at org.apache.tomcat.util.threads.TaskThread$WrappingRunnable.run(TaskThread.java:61)
    at java.lang.Thread.run(Thread.java:748)

"http-nio-8080-exec-4" Id=23 cpu=149398857 ns usr=120000000 ns blocked 0 for -1 ms waited 89 for -1 ms
   java.lang.Thread.State: RUNNABLE
    locks java.util.concurrent.ThreadPoolExecutor$Worker@370fb87a
    at sun.management.ThreadImpl.dumpThreads0(Native Method)
    at sun.management.ThreadImpl.dumpAllThreads(ThreadImpl.java:454)
    at org.apache.tomcat.util.Diagnostics.getThreadDump(Diagnostics.java:440)
    at org.apache.tomcat.util.Diagnostics.getThreadDump(Diagnostics.java:409)
    at org.apache.catalina.manager.ManagerServlet.threadDump(ManagerServlet.java:562)
    at org.apache.catalina.manager.ManagerServlet.doGet(ManagerServlet.java:376)
    at javax.servlet.http.HttpServlet.service(HttpServlet.java:622)
    at javax.servlet.http.HttpServlet.service(HttpServlet.java:729)
    at org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:292)
    at org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:207)
    at org.apache.tomcat.websocket.server.WsFilter.doFilter(WsFilter.java:52)
    at org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:240)
    at org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:207)
    at org.apache.catalina.filters.SetCharacterEncodingFilter.doFilter(SetCharacterEncodingFilter.java:108)
    at org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:240)
    at org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:207)
    at org.apache.catalina.core.StandardWrapperValve.invoke(StandardWrapperValve.java:213)
    at org.apache.catalina.core.StandardContextValve.invoke(StandardContextValve.java:106)
    at org.apache.catalina.authenticator.AuthenticatorBase.invoke(AuthenticatorBase.java:614)
    at org.apache.catalina.core.StandardHostValve.invoke(StandardHostValve.java:141)
    at org.apache.catalina.valves.ErrorReportValve.invoke(ErrorReportValve.java:79)
    at org.apache.catalina.valves.AbstractAccessLogValve.invoke(AbstractAccessLogValve.java:616)
    at org.apache.catalina.core.StandardEngineValve.invoke(StandardEngineValve.java:88)
    at org.apache.catalina.connector.CoyoteAdapter.service(CoyoteAdapter.java:522)
    at org.apache.coyote.http11.AbstractHttp11Processor.process(AbstractHttp11Processor.java:1095)
    at org.apache.coyote.AbstractProtocol$AbstractConnectionHandler.process(AbstractProtocol.java:672)
    at org.apache.tomcat.util.net.NioEndpoint$SocketProcessor.doRun(NioEndpoint.java:1504)
    at org.apache.tomcat.util.net.NioEndpoint$SocketProcessor.run(NioEndpoint.java:1460)
    - locked (a org.apache.tomcat.util.net.NioChannel@74ef881b) index 27 frame org.apache.tomcat.util.net.NioEndpoint$SocketProcessor.run(NioEndpoint.java:1460)
    at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)
    at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
    at org.apache.tomcat.util.threads.TaskThread$WrappingRunnable.run(TaskThread.java:61)
    at java.lang.Thread.run(Thread.java:748)

"http-nio-8080-exec-3" Id=22 cpu=152105677 ns usr=110000000 ns blocked 0 for -1 ms waited 90 for -1 ms
   java.lang.Thread.State: WAITING
    at sun.misc.Unsafe.park(Native Method)
    - waiting on (a java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject@337a3b83)
    at java.util.concurrent.locks.LockSupport.park(LockSupport.java:175)
    at java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject.await(AbstractQueuedSynchronizer.java:2039)
    at java.util.concurrent.LinkedBlockingQueue.take(LinkedBlockingQueue.java:442)
    at org.apache.tomcat.util.threads.TaskQueue.take(TaskQueue.java:103)
    at org.apache.tomcat.util.threads.TaskQueue.take(TaskQueue.java:31)
    at java.util.concurrent.ThreadPoolExecutor.getTask(ThreadPoolExecutor.java:1074)
    at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1134)
    at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
    at org.apache.tomcat.util.threads.TaskThread$WrappingRunnable.run(TaskThread.java:61)
    at java.lang.Thread.run(Thread.java:748)

"http-nio-8080-exec-2" Id=21 cpu=151189744 ns usr=120000000 ns blocked 0 for -1 ms waited 90 for -1 ms
   java.lang.Thread.State: WAITING
    at sun.misc.Unsafe.park(Native Method)
    - waiting on (a java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject@337a3b83)
    at java.util.concurrent.locks.LockSupport.park(LockSupport.java:175)
    at java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject.await(AbstractQueuedSynchronizer.java:2039)
    at java.util.concurrent.LinkedBlockingQueue.take(LinkedBlockingQueue.java:442)
    at org.apache.tomcat.util.threads.TaskQueue.take(TaskQueue.java:103)
    at org.apache.tomcat.util.threads.TaskQueue.take(TaskQueue.java:31)
    at java.util.concurrent.ThreadPoolExecutor.getTask(ThreadPoolExecutor.java:1074)
    at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1134)
    at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
    at org.apache.tomcat.util.threads.TaskThread$WrappingRunnable.run(TaskThread.java:61)
    at java.lang.Thread.run(Thread.java:748)

"http-nio-8080-exec-1" Id=20 cpu=673613721 ns usr=610000000 ns blocked 1 for -1 ms waited 90 for -1 ms
   java.lang.Thread.State: WAITING
    at sun.misc.Unsafe.park(Native Method)
    - waiting on (a java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject@337a3b83)
    at java.util.concurrent.locks.LockSupport.park(LockSupport.java:175)
    at java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject.await(AbstractQueuedSynchronizer.java:2039)
    at java.util.concurrent.LinkedBlockingQueue.take(LinkedBlockingQueue.java:442)
    at org.apache.tomcat.util.threads.TaskQueue.take(TaskQueue.java:103)
    at org.apache.tomcat.util.threads.TaskQueue.take(TaskQueue.java:31)
    at java.util.concurrent.ThreadPoolExecutor.getTask(ThreadPoolExecutor.java:1074)
    at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1134)
    at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
    at org.apache.tomcat.util.threads.TaskThread$WrappingRunnable.run(TaskThread.java:61)
    at java.lang.Thread.run(Thread.java:748)

"http-nio-8080-Acceptor-0" Id=18 cpu=155321259 ns usr=130000000 ns blocked 0 for -1 ms waited 0 for -1 ms (running in native)
   java.lang.Thread.State: RUNNABLE
    at sun.nio.ch.ServerSocketChannelImpl.accept0(Native Method)
    at sun.nio.ch.ServerSocketChannelImpl.accept(ServerSocketChannelImpl.java:422)
    at sun.nio.ch.ServerSocketChannelImpl.accept(ServerSocketChannelImpl.java:250)
    - locked (a java.lang.Object@3745a934) index 2 frame sun.nio.ch.ServerSocketChannelImpl.accept(ServerSocketChannelImpl.java:250)
    at org.apache.tomcat.util.net.NioEndpoint$Acceptor.run(NioEndpoint.java:682)
    at java.lang.Thread.run(Thread.java:748)

"http-nio-8080-ClientPoller-1" Id=17 cpu=5006313716 ns usr=3470000000 ns blocked 6 for -1 ms waited 0 for -1 ms (running in native)
   java.lang.Thread.State: RUNNABLE
    at sun.nio.ch.EPollArrayWrapper.epollWait(Native Method)
    at sun.nio.ch.EPollArrayWrapper.poll(EPollArrayWrapper.java:269)
    at sun.nio.ch.EPollSelectorImpl.doSelect(EPollSelectorImpl.java:93)
    at sun.nio.ch.SelectorImpl.lockAndDoSelect(SelectorImpl.java:86)
    - locked (a sun.nio.ch.EPollSelectorImpl@43ffe3d1) index 3 frame sun.nio.ch.SelectorImpl.lockAndDoSelect(SelectorImpl.java:86)
    at sun.nio.ch.SelectorImpl.select(SelectorImpl.java:97)
    at org.apache.tomcat.util.net.NioEndpoint$Poller.run(NioEndpoint.java:1034)
    at java.lang.Thread.run(Thread.java:748)

"http-nio-8080-ClientPoller-0" Id=16 cpu=4738256595 ns usr=3130000000 ns blocked 7 for -1 ms waited 0 for -1 ms (running in native)
   java.lang.Thread.State: RUNNABLE
    at sun.nio.ch.EPollArrayWrapper.epollWait(Native Method)
    at sun.nio.ch.EPollArrayWrapper.poll(EPollArrayWrapper.java:269)
    at sun.nio.ch.EPollSelectorImpl.doSelect(EPollSelectorImpl.java:93)
    at sun.nio.ch.SelectorImpl.lockAndDoSelect(SelectorImpl.java:86)
    - locked (a sun.nio.ch.EPollSelectorImpl@68bb373e) index 3 frame sun.nio.ch.SelectorImpl.lockAndDoSelect(SelectorImpl.java:86)
    at sun.nio.ch.SelectorImpl.select(SelectorImpl.java:97)
    at org.apache.tomcat.util.net.NioEndpoint$Poller.run(NioEndpoint.java:1034)
    at java.lang.Thread.run(Thread.java:748)

"ContainerBackgroundProcessor[StandardEngine[Catalina]]" Id=15 cpu=4933522583 ns usr=3520000000 ns blocked 0 for -1 ms waited 15786 for -1 ms
   java.lang.Thread.State: TIMED_WAITING
    at java.lang.Thread.sleep(Native Method)
    at org.apache.catalina.core.ContainerBase$ContainerBackgroundProcessor.run(ContainerBase.java:1344)
    at java.lang.Thread.run(Thread.java:748)

"NioBlockingSelector.BlockPoller-1" Id=12 cpu=4282428514 ns usr=2630000000 ns blocked 128 for -1 ms waited 0 for -1 ms (running in native)
   java.lang.Thread.State: RUNNABLE
    at sun.nio.ch.EPollArrayWrapper.epollWait(Native Method)
    at sun.nio.ch.EPollArrayWrapper.poll(EPollArrayWrapper.java:269)
    at sun.nio.ch.EPollSelectorImpl.doSelect(EPollSelectorImpl.java:93)
    at sun.nio.ch.SelectorImpl.lockAndDoSelect(SelectorImpl.java:86)
    - locked (a sun.nio.ch.EPollSelectorImpl@1626b026) index 3 frame sun.nio.ch.SelectorImpl.lockAndDoSelect(SelectorImpl.java:86)
    at sun.nio.ch.SelectorImpl.select(SelectorImpl.java:97)
    at org.apache.tomcat.util.net.NioBlockingSelector$BlockPoller.run(NioBlockingSelector.java:342)

"GC Daemon" Id=11 cpu=162551 ns usr=0 ns blocked 1 for -1 ms waited 1 for -1 ms
   java.lang.Thread.State: TIMED_WAITING
    at java.lang.Object.wait(Native Method)
    - waiting on (a sun.misc.GC$LatencyLock@2715671b)
    at sun.misc.GC$Daemon.run(GC.java:117)

"Signal Dispatcher" Id=5 cpu=79156 ns usr=0 ns blocked 0 for -1 ms waited 0 for -1 ms
   java.lang.Thread.State: RUNNABLE

"Finalizer" Id=3 cpu=9371177 ns usr=0 ns blocked 59 for -1 ms waited 60 for -1 ms
   java.lang.Thread.State: WAITING
    at java.lang.Object.wait(Native Method)
    - waiting on (a java.lang.ref.ReferenceQueue$Lock@4696a952)
    at java.lang.ref.ReferenceQueue.remove(ReferenceQueue.java:143)
    at java.lang.ref.ReferenceQueue.remove(ReferenceQueue.java:164)
    at java.lang.ref.Finalizer$FinalizerThread.run(Finalizer.java:209)

"Reference Handler" Id=2 cpu=6706662 ns usr=0 ns blocked 67 for -1 ms waited 66 for -1 ms
   java.lang.Thread.State: WAITING
    at java.lang.Object.wait(Native Method)
    - waiting on (a java.lang.ref.Reference$Lock@6a5842fb)
    at java.lang.Object.wait(Object.java:502)
    at java.lang.ref.Reference.tryHandlePending(Reference.java:191)
    at java.lang.ref.Reference$ReferenceHandler.run(Reference.java:153)

"main" Id=1 cpu=524567733 ns usr=500000000 ns blocked 0 for -1 ms waited 1 for -1 ms (running in native)
   java.lang.Thread.State: RUNNABLE
    at java.net.PlainSocketImpl.socketAccept(Native Method)
    at java.net.AbstractPlainSocketImpl.accept(AbstractPlainSocketImpl.java:409)
    at java.net.ServerSocket.implAccept(ServerSocket.java:545)
    at java.net.ServerSocket.accept(ServerSocket.java:513)
    at org.apache.catalina.core.StandardServer.await(StandardServer.java:446)
    at org.apache.catalina.startup.Catalina.await(Catalina.java:717)
    at org.apache.catalina.startup.Catalina.start(Catalina.java:663)
    at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
    at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
    at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
    at java.lang.reflect.Method.invoke(Method.java:498)
    at org.apache.catalina.startup.Bootstrap.start(Bootstrap.java:351)
    at org.apache.catalina.startup.Bootstrap.main(Bootstrap.java:485)
"""
        )

    def get_resources(self):
        """Send JNDI resource information."""
        url = urlparse(self.path)
        query_string = parse_qs(url.query)
        type_ = None
        if "type" in query_string:
            type_ = query_string["type"][0]

        if type_ == "org.apache.catalina.users.MemoryUserDatabase":
            self.send_text(
                """OK - Listed global resources of type org.apache.catalina.users.MemoryUserDatabase
UserDatabase:org.apache.catalina.users.MemoryUserDatabase"""
            )
        elif type_ == "com.example.Nothing":
            self.send_text(
                """OK - Listed global resources of type com.example.Nothing
FAIL - Encountered exception java.lang.ClassNotFoundException: com.example.Nothing"""
            )
        else:
            self.send_text(
                """OK - Listed global resources of type org.apache.catalina.users.MemoryUserDatabase
UserDatabase:org.apache.catalina.users.MemoryUserDatabase"""
            )

    def get_find_leakers(self):
        """Send a list of apps that a leaking memory."""
        url = urlparse(self.path)
        query_string = parse_qs(url.query)
        status = ""
        if "statusLine" in query_string:
            if query_string["statusLine"] == ["true"]:
                status = "OK - Memory leaks found\n"
        self.send_text(
            status
            + """/leaker1
/leaker2
/leaker1"""
        )

    def get_sessions(self):
        """Send a session information about an app."""
        path = self.ensure_path("Invalid context path null was specified")
        if path:
            self.send_text(
                """OK - Session information for application at context path /manager
Default maximum session inactive interval 30 minutes
<1 minutes: 1 sessions"""
            )

    ###
    #
    # the action commands, i.e. commands that actually effect some change on
    # the server
    #
    ###
    def get_expire(self):
        """Expire idle sessions in an application."""
        path = self.ensure_path("Invalid context path null was specified")
        if path:
            self.send_text(
                """OK - Session information for application at context path /manager
Default maximum session inactive interval 30 minutes
<1 minutes: 1 sessions
>15 minutes: 0 sessions were expired"""
            )

    def get_start(self):
        """Start an application."""
        path = self.ensure_path("Invalid context path null was specified")
        if path:
            self.send_text("OK - Started application at context path {}".format(path))

    def get_stop(self):
        """Stop an application."""
        path = self.ensure_path("Invalid context path null was specified")
        if path:
            self.send_text("OK - Stopped application at context path {}".format(path))

    def get_reload(self):
        """Stop and start an application."""
        path = self.ensure_path("Invalid context path null was specified")
        if path:
            self.send_text("OK - Reloaded application at context path {}".format(path))

    def put_deploy(self):
        """Deploy a tomcat application from an incoming stream."""
        path = self.ensure_path("Invalid parameters supplied for command [/deploy]")
        if path:
            length = int(self.headers.get("Content-Length"))
            self.rfile.read(length)
            self.send_text("OK - Deployed application at context path {}".format(path))

    def get_deploy(self):
        """Deploy a tomcat application already in a war file on the server."""
        url = urlparse(self.path)
        query_string = parse_qs(url.query)

        path = self.ensure_path("Invalid parameters supplied for command [/deploy]")
        if path:
            war = query_string.get("war", None)
            context = query_string.get("config", None)

            if context:
                self.send_text(
                    "OK - Deployed application at context path {}".format(path)
                )
            else:
                if war:
                    self.send_text(
                        "OK - Deployed application at context path {}".format(path)
                    )
                else:
                    self.send_text(
                        "FAIL - Invalid parameters supplied for command [/deploy]"
                    )

    def get_undeploy(self):
        """Remove an application from the server."""
        path = self.ensure_path("Invalid context path null was specified")
        if path:
            self.send_text(
                "OK - Undeployed application at context path {}".format(path)
            )
