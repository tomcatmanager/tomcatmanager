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

import urllib.request
import urllib.parse
import codecs
import requests

class ExtendedRequest(urllib.request.Request):
	def __init__(self, url, data=None, headers={}, origin_req_host=None, unverifiable=False):
		urllib.request.Request.__init__(self, url, data, headers, origin_req_host,  unverifiable)
		self.method = None

	def get_method(self):
		if self.method == None:
			if self.data:
				return "POST"
			else:
				return "GET"
		else:
			return self.method

class TomcatException(Exception):
	def __init__(self, msg):
		self.message = msg

	def __str__(self):
		return self.message

class TomcatManager:
	"""A wrapper around the tomcat manager web application
	
	"""
	def __init__(self, url="http://localhost:8080/manager", userid=None, password=None):
		self.__managerURL = url
		self.__userid = userid
		self.__password = password
		self.has_connected = False
		
		if userid and password:
			self.__passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
			self.__passman.add_password(None, self.__managerURL, self.__userid, self.__password)
			self.__auth_handler = urllib.request.HTTPBasicAuthHandler(self.__passman)
			self.__opener = urllib.request.build_opener(self.__auth_handler)
		else:
			self.__opener = urllib.request.build_opener()

	def _execute(self, cmd, params=None, data=None, headers={}, method=None):
		"""execute a tomcat command and check status returning a file obj
		for further processing
		
			tm = TomcatManager(url)
			fobj = tm._execute(url)
		"""
		url = self.__managerURL + '/text/' + cmd
		if params:
			url = url + '?%s' % urllib.parse.urlencode(params)
		req = ExtendedRequest(url, data, headers)
		if method:
			req.method = method
		response = self.__opener.open(req)
		content = codecs.iterdecode(response, 'utf-8')
		status = next(content).rstrip()
		self.has_connected = True
		if not status[:4] == 'OK -':
			raise TomcatException(status)
		return content

	def _execute_list(self, cmd, params=None, data=None, headers={}, method=None):
		"""execute a tomcat command, and return the results as a python list, one line
		per list item
		
			tm = TomcatManager(url)
			output = tm._execute_list("vminfo")
		"""
		response = self._execute(cmd, params, data, headers, method)
		output = []
		for line in response:
			output.append(line.rstrip())
		return output	

	def is_connected(self):
		"""try and connect to the tomcat server using url and authentication
		
		returns true if successful, false otherwise
		"""
		url = self.__managerURL + '/text/list'
		r = requests.get(url, auth=(self.__userid, self.__password))
		connected = False
		if (r.status_code == requests.codes.ok):
			status = r.text[:4]
			if status == 'OK -':
				connected = True
		return connected
		
	def serverinfo(self):
		"""get information about the server
		
			tm = TomcatManager(url)
			sinfo = tm.serverinfo()
		
		returns a dictionary of server information items
		"""
		response = self._execute("serverinfo")
		serverinfo = {}
		for line in response:
			key, value = line.rstrip().split(":",1)
			serverinfo[key] = value.lstrip()
		return serverinfo

	def vminfo(self):
		"""get diagnostic information about the JVM
				
			tm = TomcatManager(url)
			vminfo = tm.vminfo()
		
		returns an array of JVM information
		"""
		return self._execute_list("vminfo")

	def sslConnectorCiphers(self):
		"""get SSL/TLS ciphers configured for each connector

			tm = TomcatManager(url)
			vminfo = tm.vminfo()
		
		returns a list of JVM information
		"""
		return self._execute_list("sslConnectorCiphers")

	def threaddump(self):
		"""get a jvm thread dump

			tm = TomcatManager(url)
			dump = tm.threaddump()
		
		returns a list, one line of the thread dump per list item		
		"""
		return self._execute_list("threaddump")

	def findleaks(self):
		"""find apps that leak memory
		
		This command triggers a full garbage collection on the server. Use with
		extreme caution on production systems.
		
		Explicity triggering a full garbage collection from code is documented to be
		unreliable. Furthermore, depending on the jvm, there are options to disable
		explicit GC triggering, like ```-XX:+DisableExplicitGC```. If you want to make
		sure this command triggered a full GC, you will have to verify using something
		like GC logging or JConsole.
		
			tm = TomcatManager(url)
			leakers = tm.findleaks()

		returns a list of apps that are leaking memory. An empty list means no leaking
		apps were found.
		"""
		return self._execute_list("findleaks", {'statusLine': 'true'})

	def status(self):
		"""get server status information in XML format
		
		Uses the '/manager/status/all?XML=true' command
		
		Tomcat 8 doesn't include application info in the XML, even though the docs
		say it does.
		
			tm = TomcatManager(url)
			status = tm.status()
		
		returns a list, one line of the XML document per list item
		"""
		# this command isn't inside the /manager/text url, and it doesn't
		# return and "OK -" first line status, so we can't use _execute()
		url = self.__managerURL + '/status/all'
		params = {'XML': 'true'}
		url = url + "?%s" % urllib.parse.urlencode(params)
		req = ExtendedRequest(url)
		response = self.__opener.open(req)
		content = codecs.iterdecode(response, 'utf-8')
		self.has_connected = True
		status = []
		for line in content:
			status.append(line.rstrip())
		return status
		
	def list(self):
		"""return a list of all applications currently installed
		
			tm = TomcatManager(url)
			apps = tm.list()
		
		apps is a list of tuples: (path, status, sessions, directory)
		
		path - the relative URL where this app is deployed on the server
		status - whether the app is running or not
		sessions - number of currently active sessions
		directory - the directory on the server where this app resides
		
		"""
		response = self._execute("list")
		apps = []
		for line in response:
			apps.append(line.rstrip().split(":"))		
		self.apps = apps
		return apps

	def stop(self, path):
		"""stop an application
		
			tm = TomcatManager(url)
			tm.stop("/myappname")
		"""
		response = self._execute("stop", {'path': path})

	def start(self, path):
		"""start a stopped application
		
			tm = TomcatManager(url)
			tm.start("/myappname")
		"""
		response = self._execute("start", {'path': path})

	def reload(self, path):
		"""reload an application
		
			tm = TomcatManager(url)
			tm.reload("/myappname")
		"""
		response = self._execute("reload", {'path': path})

	def sessions(self, path):
		"""return a list of the sessions in an application
		
			tm = TomcatManager(url)
			print(tm.sessions("/myappname"))
		"""
		response = self._execute("sessions", {'path': path})
		sessions = []
		for line in response:
			sessions.append(line.rstrip())
		return sessions

	def expire(self, path, idle):
		"""expire sessions idle for longer than idle minutes
		
		Arguments:
		path     the path to the app on the server whose sessions you want to expire
		idle      sessions idle for more than this number of minutes will be expired
		         use age=0 to expire all sessions
		"""
		response = self._execute("expire", {'path': path, 'idle': idle})
		sessions = []
		for line in response:
			sessions.append(line.rstrip())
		return sessions

	def deployWAR(self, path, fileobj, update=False, tag=None):
		"""read a WAR file from a local fileobj and deploy it at path
		
		Arguments:
		path     the path on the server to deploy this war to
		fileobj  a file object opened for binary reading, from which the war file will be read
		update   whether to update the existing path (default False)
		tag      a tag for this application (default None)
		 
		"""
		wardata = fileobj.read()
		headers = {}
		headers['Content-type'] = "application/octet-stream"
		headers['Content-length'] = str(len(wardata))
		params = {'path': path}
		if update:
			params['update'] = "true"
		if tag:
			params['tag'] = tag
		response = self._execute("deploy", params, wardata, headers, "PUT")
	
	def deployLocalWAR(self, path, warfile, config=None, update=False, tag=None):
		"""tell tomcat to deploy a file already on the server"""
		pass

	def undeploy(self, path):
		"""undeploy an application
		
			tm = TomcatManager(url)
			tm.undeploy("/myappname")
		"""
		response = self._execute("undeploy", {'path': path})

	def resources(self,type=None):
		"""list the global JNDI resources available for use in resource links for config files
		
		Arguments:
		type	a fully qualified Java class name of the resource type you are interested in
				if passed empty, resources of all types will be returned
		"""
		if type:
			response = self._execute("resources", {'type': type})
		else:
			response = self._execute("resources")
		resources = []
		for line in response:
			resources.append(line.rstrip())
		return resources
