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
import collections

from .models import codes, TomcatManagerResponse, ServerInfo


class TomcatManager:
	"""
	A class for interacting with the Tomcat Manager web application.
	
	
	Here's a summary of the recommended way to use this class with proper exception
	and error handling. For this example, we'll use the :meth:`server_info` method.
	
	>>> import tomcatmanager as tm
	>>> tomcat = tm.TomcatManager(url='http://localhost:8080/manager', \
	... 	userid='ace', password='newenglandclamchowder')
	>>> try:
	... 	r = tomcat.server_info()
	...		r.raise_for_status()
	...		if r.ok:
	...			print(r.server_info)
	...		else:
	...			print('Error: {}'.format(r.status_message))
	... except Exception as err:
	... 	print('Error: {}'.format(err))
	"""

	@classmethod
	def _is_stream(self, obj):
		"""return True if passed a stream type object"""
		return all([
			hasattr(obj, '__iter__'),
			not isinstance(obj, (str, bytes, list, tuple, collections.Mapping))
		])
		
	def __init__(self, url=None, userid=None, password=None):
		"""
		Initialize a new TomcatManager object.
		
		:param url: URL where the Tomcat Manager web application is deployed
		:param userid: userid to authenticate
		:param password: password to authenticate

		Initializing the object with a url and credentials does not try to connect
		to the server. Use the :meth:`connect` method for that.
		
		Usage::
		
		>>> import tomcatmanager as tm
		>>> tomcat = tm.TomcatManager('http://localhost:8080/manager', \
		... 	'ace', 'newenglandclamchowder')
		
		or
		
		>>> import tomcatmanager as tm
		>>> tomcat = tm.TomcatManager(url='http://localhost:8080/manager', \
		... 	userid='ace', password='newenglandclamchowder')
		
		or
		
		>>> import tomcatmanager as tm
		>>> tomcat = tm.TomcatManager()
		"""
		self._url = url
		self._userid = userid
		self._password = password

	def _get(self, cmd, payload=None):
		"""make an HTTP get request to the tomcat manager web app
		
		returns a TomcatManagerResponse object
		"""
		base = self._url or ''
		url = base + '/text/' + cmd
		r = TomcatManagerResponse()
		r.response = requests.get(
				url,
				auth=(self._userid, self._password),
				params=payload
				)
		return r

	###
	#
	# convenience and utility methods
	#
	###
	def connect(self, url=None, userid=None, password=None):
		"""
		Connect to a Tomcat Manager server.
		
		:param url: url where the Tomcat Manager web application is deployed
		:param userid: userid to authenticate
		:param password: password to authenticate
		:return: :class:`TomcatManagerResponse <TomcatManagerResponse>` object
		
		You don't have to connect before using any other commands. If you initialized
		the object with credentials you can call any other method. The purpose
		of :meth:`connect` is to:
		
		- give you a way to change the credentials on an existing object
		- provide a convenient mechanism to validate you can actually connect to the server
		
		Usage::
		
		>>> import tomcatmanager as tm
		>>> tomcat = tm.TomcatManager()
		>>> r = tomcat.connect('http://localhost:8080/manager', \
		... 	'ace', 'newenglandclamchowder')
		
		or
		
		>>> import tomcatmanager as tm
		>>> tomcat = tm.TomcatManager(url='http://localhost:8080/manager', \
		... 	userid='ace', password='newenglandclamchowder')
		>>> r = tomcat.connect()
		
		The only way to validate whether we are connected is to actually
		get a url. Internally this method tries the 'serverinfo' command.
		
		Requesting url's via http can raise all kinds of exceptions. For
		example, if you give a URL where no web server is listening, you'll get a
		:meth:`requests.connections.ConnectionError`. However, :meth:`connect`
		won't raise exceptions for everything. If the credentials are
		incorrect, you won't get an exception unless you ask for it. To check
		whether you are actually connected, use::
		
		>>> tomcat.is_connected
		
		If you want to raise exceptions see
		:meth:`tomcatmanager.models.TomcatManagerResponse.raise_for_status`.
		"""
		self._url = url
		self._userid = userid
		self._password = password
		r = self._get('serverinfo')
		# hide the fact that we did a different command, we don't
		# want people relying on or using this data
		r.result = ''
		r.status_message = ''
		return r

	@property
	def is_connected(self):
		"""
		Is the url an actual tomcat server and are the credentials valid?
		
		:return: True if connected to a tomcat server, False if not.
		"""
		try:
			r = self._get('list')
			return r.ok
		except:
			return False

	###
	#
	# The info commands. These commands that don't affect change, they just
    # return some information from the server.
	#
	###
	def list(self):
		"""
		list of all applications currently installed

		:return: :class:`TomcatManagerResponse <TomcatManagerResponse>` object
		
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
		tmr = self._get('list')
		apps = []
		for line in tmr.result:
			apps.append(line.rstrip().split(":"))		
		tmr.apps = apps
		return tmr
		
	def server_info(self):
		"""get information about the server
		
			tm = TomcatManager(url)
			r = tm.serverinfo()
			r.server_info['OS Name']
			
		returns an instance of TomcatManagerResponse with an additional server_info
		attribute. The server_info attribute is a dictionary of items about the server
		"""
		r = self._get('serverinfo')
		r.server_info = ServerInfo(r.result)
		return r

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
		base = self._url or ''		
		url = base + '/status/all'
		tmr = TomcatManagerResponse()
		tmr.response = requests.get(
				url,
				auth=(self._userid, self._password),
				params={'XML': 'true'}
				)
		tmr.result = tmr.response.text.splitlines()
		tmr.status_xml = tmr.result

		# we have to force a status_code and a status_message
		# because the server doesn't return them
		if tmr.response.status_code == requests.codes.ok:
			tmr.status_code = codes.ok
			tmr.status_message = codes.ok
		else:
			tmr.status_code = codes.fail
			tmr.status_message = codes.fail
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
		tmr = self._get('vminfo')
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
		tmr = self._get('sslConnectorCiphers')
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
		tmr = self._get('threaddump')
		tmr.thread_dump = tmr.result
		return tmr

	def resources(self, type=None):
		"""list the global JNDI resources available for use in resource links for context config files
		
			tm = TomcatManager(url)
			r = tm.resources()
			resources = r.resources
		
		pass the optional fully qualified java class name of the resource type you are
		interested in. For example, you might pass javax.sql.DataSource to acquire
		the names of all available JDBC data sources
		
		returns an instance of TomcatManagerResponse with an additional resources
		attribute
		
		resources is a list of tuples: (resource, class)
		"""
		if type:
			r = self._get('resources', {'type': str(type)})
		else:
			r = self._get('resources')

		resources = {}
		for line in r.result:
			resource, classname = line.rstrip().split(':',1)
			if resource[:7] != codes.fail + ' - ':
				resources[resource] = classname.lstrip()
		r.resources = resources
		return r


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
		tmr = self._get('findleaks', {'statusLine': 'true'})
		leakers = []
		for line in tmr.result:
			leakers.append(line.rstrip())
		# remove duplicates by changing it to a set, then back to a list		
		tmr.leakers = list(set(leakers))
		return tmr

	def sessions(self, path, version=None):
		"""return a list of the sessions in an application at a given path
	
			tm = TomcatManager(url)
			tmr = tm.sessions('/manager')
			x = tmr.result
			y = tmr.sessions
		
		returns an instance of TomcatManagerResponse with the session summary in the
		result attribute and in the sessions attribute
		"""
		params = {}
		params['path'] = path
		if version:
			params['version'] = version
		r = self._get('sessions', params)
		if r.ok: r.sessions = r.result
		return r

	###
	#
	# The action commands. These commands affect some change on the server.
	#
	###
	def expire(self, path, version=None, idle=None):
		"""
		Expire sessions idle for longer than idle minutes.
		
		:param path: the path to the app on the server whose sessions you want to expire
		:param idle: sessions idle for more than this number of minutes will be
		expired. Use idle=0 to expire all sessions.
		:return: an instance of TomcatManagerResponse with the session summary in the
		result attribute and in the sessions attribute
		
		>>> tm = TomcatManager(url)
		>>> r = tm.sessions('/manager')
		>>> x = r.result
		>>> y = r.sessions
		"""
		params = {}
		params['path'] = path
		if version:
			params['version'] = version
		if idle:
			params['idle'] = idle		
		r = self._get('expire', params)
		if r.ok: r.sessions = r.result
		return r
	
	def start(self, path, version=None):
		"""start the application at a given path
	
			tm = TomcatManager(url)
			tmr = tm.start('/someapp')
			tmr.raise_on_status()
		
		returns an instance of TomcatManagerResponse
		"""
		params = {}
		params['path'] = path
		if version:
			params['version'] = version
		return self._get('start', params)

	def stop(self, path, version=None):
		"""stop the application at a given path
	
			tm = TomcatManager(url)
			tmr = tm.stop('/someapp')
			tmr.raise_on_status()
		
		returns an instance of TomcatManagerResponse
		"""
		params = {}
		params['path'] = path
		if version:
			params['version'] = version
		return self._get('stop', params)

	def reload(self, path, version=None):
		"""reload the application at a given path
	
			tm = TomcatManager(url)
			tmr = tm.reload('/someapp')
			tmr.raise_on_status()
		
		returns an instance of TomcatManagerResponse
		"""
		params = {}
		params['path'] = path
		if version:
			params['version'] = version
		return self._get('reload', params)

	def deploy(self, path, localwar=None, serverwar=None, version=None, update=False):
		"""
		Deploy an application to the Tomcat server.
		
		If the WAR file is already present somewhere on the same server
		where Tomcat is running, you should use the ``serverwar`` parameter. If
		the WAR file is local to where python is running, use the ``localwar``
		parameter. Specify either ``localwar`` or ``serverwar``, but not both. 
		
		:param path: The path on the server to deploy this war to, i.e. /sampleapp
		:param localwar: (optional) The path (specified using your particular
			operating system convention) to a war file on the local file system. This
			will be sent to the server for deployment.
		:param serverwar: (optional) The java-style path (use slashes not backslashes) to
			the war file on the server. Don't include ``file:`` at the beginning.
		:param version: (optional) For tomcat parallel deployments, the version to use
			for this version of the app
		:param update: (optional) Whether to undeploy the existing path
			first (default False)
		:return: :class:`TomcatManagerResponse <TomcatManagerResponse>` object
		
		
		"""
		params = {}
		params['path'] = path
		if update:
			params['update'] = 'true'
		if version:
			params['version'] = version

		if localwar and serverwar:
			raise ValueError('can not deploy localwar and serverwar at the same time')
		elif localwar:
			# PUT a local stream
			base = self._url or ''
			url = base + '/text/deploy'
			if self._is_stream(localwar):
				warobj = localwar
			else:
				warobj = open(localwar, 'rb')	

			r = TomcatManagerResponse()
			r.response = requests.put(
					url,
					auth=(self._userid, self._password),
					params=params,
					data=warobj,
					)
		elif serverwar:
			params['war'] = serverwar
			r = self._get('deploy', params)
		else:
			r = self._get('deploy', params)

		return r

	def undeploy(self, path, version=None):
		"""Undeploy the application at a given path
		
		:param path: The path of the application to undeploy
		:param version: The version to undeploy
		:return: :class:`TomcatManagerResponse <TomcatManagerResponse>` object
		:rtype: tomcatmanager.TomcatManagerResponse		
				
		If an application was deployed using a version, then a version is required to
		undeploy the application.
		"""
		params = {'path': path}
		if version:
			params['version'] = version
		return self._get('undeploy', params)
