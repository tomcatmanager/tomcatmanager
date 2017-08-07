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

USERID='admin'
PASSWORD='admin'

class MockRequestHandler(BaseHTTPRequestHandler):

	AUTH_KEY = base64.b64encode('{u}:{p}'.format(u=USERID, p=PASSWORD).encode('utf-8')).decode('utf-8')
	TEXT_PATTERN = re.compile(r'^/manager/text/?$')
	LIST_PATTERN = re.compile(r'^/manager/text/list$|\?')
	SERVERINFO_PATTERN = re.compile(r'^/manager/text/serverinfo$|\?')
	
	def do_GET(self):
		# first check authentication
		if self.headers.get('Authorization') != 'Basic '+self.AUTH_KEY:
			self.send_response(requests.codes.unauthorized)
			self.send_header('WWW-Authenticate','Basic realm=\"tomcatmanager\"')
			self.send_header('Content-type', 'text/html')
			self.end_headers()
			c = "not authorized"
			self.wfile.write(c.encode('utf-8'))
			return
		
		# now handle the url
		if re.search(self.TEXT_PATTERN, self.path):
			self.send_response(requests.codes.ok)
			self.send_header('Content-type', 'text/html')
			self.end_headers()
			c = 'FAIL - Unknown command'
			self.wfile.write(c.encode('utf-8'))
		elif re.search(self.LIST_PATTERN, self.path):
			self.get_list()
		elif re.search(self.SERVERINFO_PATTERN, self.path):
			self.get_serverinfo()
		else:
			# the path wasn't found, tomcat sends a 200 with a FAIL
			self.send_response(requests.codes.ok)
			self.send_header('Content-type', 'text/html')
			self.end_headers()
			c = 'FAIL - Unknown command'
			self.wfile.write(c.encode('utf-8'))

	def send_text(self, content):
		"""send a status ok and content as text/html"""
		self.send_response(requests.codes.ok)
		self.send_header('Content-type', 'text/html')
		self.end_headers()
		self.wfile.write(content.encode('utf-8'))
		
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
	


#
#
def start_mock_server():
	"""start a mock Tomcat Manager application
	
	returns the (url, userid, password) where the server is accessible
	"""

	s = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
	s.bind(('localhost', 0))
	address, port = s.getsockname()
	s.close()

	url = 'http://localhost:{port}/manager'.format(port=port)
		
	mock_server = HTTPServer(('localhost', port), MockRequestHandler)
	mock_server_thread = Thread(target=mock_server.serve_forever)
	mock_server_thread.setDaemon(True)
	mock_server_thread.start()
    
	return (url, USERID, PASSWORD)
