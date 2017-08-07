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
