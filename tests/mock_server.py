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

"""Mock up a Tomcat Manager server
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
from threading import Thread
import requests
import re
import base64
from urllib.parse import urlparse
from urllib.parse import parse_qs

USERID='admin'
PASSWORD='admin'

class MockRequestHandler80(BaseHTTPRequestHandler):
	"""Handle HTTP Requests like Tomcat Manager 8.0.x"""

	AUTH_KEY = base64.b64encode('{u}:{p}'.format(u=USERID, p=PASSWORD).encode('utf-8')).decode('utf-8')
	TEXT_PATTERN = re.compile(r'^/manager/text/?$')
	LIST_PATTERN = re.compile(r'^/manager/text/list($|\?.*$)')
	SERVERINFO_PATTERN = re.compile(r'^/manager/text/serverinfo($|\?.*$)')
	DEPLOY_PATTERN = re.compile(r'^/manager/text/deploy($|\?.*$)')
	UNDEPLOY_PATTERN = re.compile(r'^/manager/text/undeploy($|\?.*$)')
	STATUS_PATTERN = re.compile(r'^/manager/status(/|/all)?($|\?.*$)')


	def do_GET(self):
		if not self.authorized(): return
				
		# handle request based on path
		if re.search(self.TEXT_PATTERN, self.path):
			self.send_fail('Unknown command')
		elif re.search(self.LIST_PATTERN, self.path):
			self.get_list()
		elif re.search(self.SERVERINFO_PATTERN, self.path):
			self.get_serverinfo()
		elif re.search(self.DEPLOY_PATTERN, self.path):
			self.send_fail('Invalid parameters supplied for command [/deploy]')
		elif re.search(self.UNDEPLOY_PATTERN, self.path):
			self.get_undeploy()
		elif re.search(self.STATUS_PATTERN, self.path):
			self.get_status()
		else:
			self.send_fail('Unknown command')

	def do_PUT(self):
		if not self.authorized(): return

		# handle request based on path
		if re.search(self.DEPLOY_PATTERN, self.path):
			self.put_deploy()
		else:
			self.send_fail('Unknown command')
			
	def authorized(self):
		"""check authorization and return true or false"""
		# first check authentication
		if self.headers.get('Authorization') == 'Basic '+self.AUTH_KEY:
			return True
		else:
			self.send_response(requests.codes.unauthorized)
			self.send_header('WWW-Authenticate','Basic realm=\"tomcatmanager\"')
			self.send_header('Content-type', 'text/html')
			self.end_headers()
			c = "not authorized"
			self.wfile.write(c.encode('utf-8'))
			return False
	
	def send_fail(self, msg=None):
		# the path wasn't found, tomcat sends a 200 with a FAIL
		self.send_text('FAIL - {msg}'.format(msg=msg))

	def send_text(self, content):
		"""send a status ok and content as text/html"""
		self.send_response(requests.codes.ok)
		self.send_header('Content-type', 'text/html')
		self.end_headers()
		self.wfile.write(content.encode('utf-8'))

	#
	#
	def get_list(self):
		self.send_text("""OK - Listed applications for virtual host localhost
/:running:0:ROOT
/host-manager:running:0:/usr/share/tomcat8-admin/host-manager
/manager:running:0:/usr/share/tomcat8-admin/manager""")

	def get_serverinfo(self):
		self.send_text("""OK - Server info
Tomcat Version: Apache Tomcat/8.0.32 (Ubuntu)
OS Name: Linux
OS Version: 4.4.0-89-generic
OS Architecture: amd64
JVM Version: 1.8.0_131-8u131-b11-2ubuntu1.16.04.3-b11
JVM Vendor: Oracle Corporation""")
	
	def get_status(self):
		self.send_text("""<?xml version="1.0" encoding="utf-8"?><?xml-stylesheet type="text/xsl" href="/manager/xform.xsl" ?>
<status><jvm><memory free='22294576' total='36569088' max='129761280'/><memorypool name='CMS Old Gen' type='Heap memory' usageInit='22413312' usageCommitted='25165824' usageMax='89522176' usageUsed='13503656'/><memorypool name='Par Eden Space' type='Heap memory' usageInit='8912896' usageCommitted='10158080' usageMax='35782656' usageUsed='299600'/><memorypool name='Par Survivor Space' type='Heap memory' usageInit='1114112' usageCommitted='1245184' usageMax='4456448' usageUsed='473632'/><memorypool name='Code Cache' type='Non-heap memory' usageInit='2555904' usageCommitted='12713984' usageMax='251658240' usageUsed='12510656'/><memorypool name='Compressed Class Space' type='Non-heap memory' usageInit='0' usageCommitted='2621440' usageMax='1073741824' usageUsed='2400424'/><memorypool name='Metaspace' type='Non-heap memory' usageInit='0' usageCommitted='24903680' usageMax='-1' usageUsed='24230432'/></jvm><connector name='"http-nio-8080"'><threadInfo  maxThreads="200" currentThreadCount="10" currentThreadsBusy="1" /><requestInfo  maxTime="570" processingTime="2015" requestCount="868" errorCount="494" bytesReceived="0" bytesSent="1761440" /><workers><worker  stage="S" requestProcessingTime="1" requestBytesSent="0" requestBytesReceived="0" remoteAddr="192.168.13.22" virtualHost="192.168.13.66" method="GET" currentUri="/manager/status/all" currentQueryString="XML=true" protocol="HTTP/1.1" /><worker  stage="R" requestProcessingTime="0" requestBytesSent="0" requestBytesReceived="0" remoteAddr="&#63;" virtualHost="&#63;" method="&#63;" currentUri="&#63;" currentQueryString="&#63;" protocol="&#63;" /></workers></connector></status>
		""")

	def put_deploy(self):
		# verify we have a path query string
		url = urlparse(self.path)
		qs = parse_qs(url.query)
		if 'path' in qs:
			path = qs['path']
			length = int(self.headers.get('Content-Length'))
			content = self.rfile.read(length)
			self.send_text('OK - Deployed application at context path {path}'.format(path=path))
		else:
			self.send_fail('Invalid parameters supplied for command [/deploy]')

	def get_undeploy(self):
		# verify we have a path query string
		url = urlparse(self.path)
		qs = parse_qs(url.query)
		if 'path' in qs:
			path = qs['path']
			self.send_text('OK - Undeployed application at context path {path}'.format(path=path))
		else:
			self.send_fail('Invalid parameters supplied for command [/deploy]')
	
#
#
def start_mock_server80():
	"""start a mock Tomcat Manager application
	
	returns the (url, userid, password) where the server is accessible
	"""

	s = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
	s.bind(('localhost', 0))
	address, port = s.getsockname()
	s.close()

	url = 'http://localhost:{port}/manager'.format(port=port)
		
	mock_server = HTTPServer(('localhost', port), MockRequestHandler80)
	mock_server_thread = Thread(target=mock_server.serve_forever)
	mock_server_thread.setDaemon(True)
	mock_server_thread.start()
    
	return (url, USERID, PASSWORD)
