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


class TomcatManagerResponse:
	"""The response for a Tomcat Manager command"""    

	def __init__(self, response=None):
		self._response = response
		self._status_code = None
		self._status_message = None
		self._result = None

	@property
	def response(self):
		"""contains the requsts.Response object from our request"""
		return self._response

	@response.setter
	def response(self, value):
		self._response = value

	@property
	def status_code(self):
		"""status of the tomcat manager command, can be 'OK' or 'FAIL'"""
		return self._status_code

	@status_code.setter
	def status_code(self, value):
		self._status_code = value

	@property
	def status_message(self):
		return self._status_message
	
	@status_message.setter
	def status_message(self, value):
		self._status_message = value

	@property
	def result(self):
		return self._result

	@result.setter
	def result(self, value):
		self._result = value

	def raise_for_status(self):
		"""raise exceptions if status is not ok
		
		first calls requests.Response.raise_for_status() which will
		raise exceptions if a 4xx or 5xx response is received from the server
		
		If that doesn't raise anything, then check if we have an "FAIL" response
		from the first line of text back from the Tomcat Manager web app, and
		raise an TomcatException if necessary
		
		stole idea from requests package
		"""
		self.response.raise_for_status()
		if self.status_code == 'FAIL':
			raise TomcatException(self.status_message)


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
		if status[:4] != 'OK -':
			raise TomcatException(status)
		return content
	
	def _get(self, cmd, payload=None):
		"""make an HTTP get request to the tomcat manager web app
		
		returns a TomcatManagerResponse object
		"""
		url = self.__managerURL + '/text/' + cmd
		tmr = TomcatManagerResponse()
		tmr.response = requests.get(
				url,
				auth=(self.__userid, self.__password),
				params=payload
				)
		# set the other attributes of the response object
		statusline = tmr.response.text.splitlines()[0]
		tmr.status_code = statusline.split(' ', 1)[0]
		tmr.status_message = statusline.split(' ',1)[1][2:]
		tmr.result = tmr.response.text.splitlines()[1:]
		return tmr

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

	###
	#
	# convenience and utility methods
	#
	###
	def is_connected(self):
		"""try and connect to the tomcat server using url and authentication
		
		returns true if successful, false otherwise
		"""
		tmr = self._get("list")
		connected = False
		if (tmr.response.status_code == requests.codes.ok):
			if tmr.status_code == 'OK':
				connected = True
		return connected

	###
	#
	# the info commands, i.e. commands that don't really do anything, they
	# just return some information from the server
	#
	###
	def list(self):
		"""list of all applications currently installed
		
			tm = TomcatManager(url)
			tmr = tm.list()
			apps = tmr.apps
		
		returns an instance of TomcatManagerResponse with an additional apps
		attribute
		
		apps is a list of tuples: (path, status, sessions, directory)
		
		path - the relative URL where this app is deployed on the server
		status - whether the app is running or not
		sessions - number of currently active sessions
		directory - the directory on the server where this app resides		
		"""
		tmr = self._get("list")
		apps = []
		for line in tmr.result:
			apps.append(line.rstrip().split(":"))		
		tmr.apps = apps
		return tmr
		
	def server_info(self):
		"""get information about the server
		
			tm = TomcatManager(url)
			tmr = tm.serverinfo()
			tmr.server_info['OS Name']
			
		returns an instance of TomcatManagerResponse with an additional server_info
		attribute. The server_info attribute is a dictionary of items about the server
		"""
		tmr = self._get("serverinfo")
		sinfo = {}
		for line in tmr.result:
			key, value = line.rstrip().split(":",1)
			sinfo[key] = value.lstrip()
		tmr.server_info = sinfo
		return tmr

	def status_xml(self):
		"""get server status information in XML format
		
		we have lots of status stuff, so this method is named status_xml to try
		and reduce confusion with status_code and status_message
		
		Uses the '/manager/status/all?XML=true' command
		
		Tomcat 8 doesn't include application info in the XML, even though the docs
		say it does.
		
			tm = TomcatManager(url)
			tmr = tm.status_xml()
			x = tmr.result
			y = tmr.status_xml
		
		returns an instance of TomcatManagerResponse with the status xml document in
		the result attribute and in the status_xml attribute
		"""
		# this command isn't in the /manager/text url space, so we can't use _get()
		url = self.__managerURL + '/status/all'
		tmr = TomcatManagerResponse()
		tmr.response = requests.get(
				url,
				auth=(self.__userid, self.__password),
				params={'XML': 'true'}
				)
		tmr.result = tmr.response.text.splitlines()
		tmr.status_xml = tmr.result

		# we have to force a status_code and a status_message
		# because the server doesn't return them
		if tmr.response.status_code == requests.codes.ok:
			tmr.status_code = 'OK'
			tmr.status_message = 'ok'
		else:
			tmr.status_code = 'FAIL'
			tmr.status_message = 'fail'
		return tmr

	def vm_info(self):
		"""get diagnostic information about the JVM
				
			tm = TomcatManager(url)
			tmr = tm.vm_info()
			x = tmr.result
			y = tmr.vm_info
		
		returns an instance of TomcatManagerResponse with the virtual machine info in
		the result attribute and in the vm_info attribute
		"""
		tmr = self._get("vminfo")
		tmr.vm_info = tmr.result
		return tmr

	def ssl_connector_ciphers(self):
		"""get SSL/TLS ciphers configured for each connector

			tm = TomcatManager(url)
			tmr = tm.ssl_connector_ciphers()
			x = tmr.result
			y = tmr.ssl_connector_info
		
		returns an instance of TomcatManagerResponse with the ssl cipher info in the
		result attribute and in the ssl_connector_info attribute
		"""
		tmr = self._get("sslConnectorCiphers")
		tmr.ssl_connector_ciphers = tmr.result
		return tmr

	def thread_dump(self):
		"""get a jvm thread dump

			tm = TomcatManager(url)
			tmr = tm.thread_dump()
			x = tmr.result
			y = tmr.thread_dump
		
		returns an instance of TomcatManagerResponse with the thread dump in the result
		attribute and in the thread_dump attribute
		"""
		tmr = self._get("threaddump")
		tmr.thread_dump = tmr.result
		return tmr

	def find_leakers(self):
		"""list apps that leak memory
		
		This command triggers a full garbage collection on the server. Use with
		extreme caution on production systems.
		
		Explicity triggering a full garbage collection from code is documented to be
		unreliable. Furthermore, depending on the jvm, there are options to disable
		explicit GC triggering, like ```-XX:+DisableExplicitGC```. If you want to make
		sure this command triggered a full GC, you will have to verify using something
		like GC logging or JConsole.
		
			tm = TomcatManager(url)
			tmr = tm.find_leaks()
			leakers = tmr.leakers

		returns an instance of TomcatManagerResponse with an additional leakers
		attribute. If leakers in an empty list, then no leaking apps were found.
		
		The tomcat manager documentation says that it can return duplicates in this
		list if the app has been reloaded and was leaking both before and after the
		reload. The list returned by the leakers attribute will have no duplicates in
		it
		
		"""
		tmr = self._get("findleaks", {'statusLine': 'true'})
		leakers = []
		for line in tmr.result:
			leakers.append(line.rstrip())
		# remove duplicates by changing it to a set, then back to a list		
		tmr.leakers = list(set(leakers))
		return tmr

	def sessions(self, path):
		"""return a list of the sessions in an application at a given path
	
			tm = TomcatManager(url)
			tmr = tm.sessions('/manager')
			x = tmr.result
			y = tmr.sessions
		
		returns an instance of TomcatManagerResponse with the session summary in the
		result attribute and in the sessions attribute
		"""
		tmr = self._get("sessions", {'path': str(path)})
		tmr.sessions = tmr.result
		return tmr

	###
	#
	# the action commands, i.e. commands that actually effect some change on
	# the server
	#
	###
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



	def deploy_war(self, path, fileobj, update=False, tag=None):
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
		
		params = {}
		if path:
			params['path'] = path
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
		params = {}
		if path:
			params['path'] = path
		response = self._execute("undeploy", params)

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
