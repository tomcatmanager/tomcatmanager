#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007, Jared Crapo
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

"""
Tomcat Manager
==============

	Manage a tomcat server from the command line or from an interactive
	shell


Command Line Use
----------------

	tomcat-manager --user=userid, --password=mypass [--debug] \\
		manager_url command [arguments]
		
	connect to the tomcat manager at manager_url, using userid and
	mypass for authentication, and run command with any supplied
	arguments.  For a list of commands enter the interactive
	shell and type "help".  For a list of the arguments for any
	command, enter the interactive shell and type "help \{command\}"


Interactive Use
---------------

	tomcat-manager [--help | -h]

		display help and exit


	tomcat-manager [--version]

		display version information and exit


	tomcat-manager [--debug]

		enter the interactive shell with debug mode enabled


	tomcat-manager --user=userid, --password=mypass [--debug] manager_url

		connect to the tomcat manager at manager_url, using userid and
		mypass for authentication, and then enter the interactive shell


	Once you are in the interactive shell, type "help" for a list of
	commands and their arguments.
	
	To view the license for this software, enter the interactive shell
	and type "help license"


Options
-------

	--user, -u        the user to use for authentication
	                  with the tomcat application

	--password, -p    the password to use for authentication
	                  with the tomcat application
	
	--debug           display stack traces when errors occur
	
	--version         display version information and exit
	
	--help, -h        display this help and exit
"""
import cmd
import getopt
import sys
import traceback
import urllib.request
import urllib.parse
import codecs
import getpass

#
#
versionString="0.4"
class Usage(Exception):
	def __init__(self, msg):
		self.message = msg

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
	"""A wrapper around the tomcat manager application
	
"""
	def __init__(self, url="http://localhost:8080/manager", userid=None, password=None):
		self.__managerURL = url
		self.__userid = userid
		self.__password = password
		self.hasConnected = False
		
		if userid and password:
			self.__passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
			self.__passman.add_password(None, self.__managerURL, self.__userid, self.__password)
			self.__auth_handler = urllib.request.HTTPBasicAuthHandler(self.__passman)
			self.__opener = urllib.request.build_opener(self.__auth_handler)
		else:
			self.__opener = urllib.request.build_opener()


	def _execute(self, cmd, params=None, data=None, headers={}, method=None):
		"""execute a tomcat command and check status returning a file obj for further processing
		
		fobj = _execute(url)
		
		"""
		url = self.__managerURL + "/" + cmd
		if params:
			url = url + "?%s" % urllib.parse.urlencode(params)
		req = ExtendedRequest(url, data, headers)
		if method:
			req.method = method
		response = self.__opener.open(req)
		content = codecs.iterdecode(response,"utf-8")
		status = next(content).rstrip()
		self.hasConnected = True
		if not status[:4] == "OK -":
			raise TomcatException(status)
		return content


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
		print tm.sessions("/myappname")
		
		"""
		response = self._execute("sessions", {'path': path})
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
		response = self._execute("resources", {'type': type})
		resources = []
		for line in response:
			resources.append(line.rstrip())
		return resources


#
#
class InteractiveTomcatManager(cmd.Cmd):
	"""an interactive command line tool for tomcat manager
	
	"""
	def __init__(self):
		cmd.Cmd.__init__(self)
		self.prompt = "tomcat-manager>"
		self.__tm = None
		self.__MSG_NotConnected = "not connected"
		self.debugFlag = False

	def docmd(self, func, *args):
		"""call a function and return, printing any exceptions that occur
		
		if we have not successfully connected, then say not connected;
		otherwise, just run the command
		
		"""

#		try:
		return func(*args)
#		except:
#			self.__printexception()

	def do_connect(self, args):
		"""connect to an instance of the manager application"""
		url = None
		username = None
		password = None
		sargs = args.split()
		try:
			if len(sargs) == 1:
				url = sargs[0]
			elif len(sargs) == 2:
				url = sargs[0]
				username = sargs[1]
				password = getpass.getpass()
			elif len(sargs) == 3:
				url = sargs[0]
				username = sargs[1]
				password = sargs[2]
			else:
				raise ValueError()

			self.__tm = TomcatManager(url, username, password)
			apps = self.__tm.list()
			self.__printstatus("connected to tomcat manager at %s" % url)
		except ValueError:
			self.help_connect()
		except urllib.request.HTTPError as e:
			if e.code == 401:
				self.__printerror("login failed")
			elif e.code == 403:
				self.__printerror("login failed")
			elif e.code == 404:
				self.__printerror("tomcat manager not found at %s" % url)
			else:
				self.__printexception()
		except TomcatException:
			self.__printexception()
		except:
			self.__printexception()

	def help_connect(self):
		print("usage: connect url [username] [password]")

	def do_list(self, args):
		"""list the applications on the server"""
		if args:
			self.help_list()
		elif self.__tm and self.__tm.hasConnected:
			apps = self.docmd(self.__tm.list)
			cw = [24, 7, 8, 36]
			# build the format string from the column widths so we only
			# have the column widths hardcoded in one place
			fmt = " ".join(list(map(lambda x: "%"+str(x)+"s",cw)))
			dashes = "-"*80
			print(fmt % ("Path".ljust(cw[0]), "Status".ljust(cw[1]), "Sessions".rjust(cw[2]), "Directory".ljust(cw[3])))
			print(fmt % (dashes[:cw[0]], dashes[:cw[1]], dashes[:cw[2]], dashes[:cw[3]]))
			for app in apps:
				path, status, session, directory = app[:4]
				print(fmt % (app[0].ljust(cw[0]), app[1].ljust(cw[1]), app[2].rjust(cw[2]), app[3].ljust(cw[3])))
		else:
			self.__printerror(self.__MSG_NotConnected)

	def help_list(self):
		print("Usage: list")
		print("list installed applications")

	def do_serverinfo(self, args):
		if args:
			self.help_list()
		elif self.__tm and self.__tm.hasConnected:
			info = self.docmd(self.__tm.serverinfo)
			for key,value in iter(sorted(info.items())):
				print("%s: %s" % (key, value))
		else:
			self.__printerror(self.__MSG_NotConnected)
	
	def help_serverinfo(self):
		print("Usage: serverinfo")
		print("show information about the server")

	def do_start(self, args):
		"""start an application"""
		if self.__tm and self.__tm.hasConnected:
			try:
				app, = args.split()
				self.docmd(self.__tm.start, app)
			except ValueError:
				self.help_start()
		else:
			self.__printerror(self.__MSG_NotConnected)

	def help_start(self):
		"""print help for the start command"""
		print("Usage: start {path}")
		print("start the application at {path}")

	def do_stop(self, args):
		"""stop an application"""
		if self.__tm and self.__tm.hasConnected:
			try:
				app, = args.split()
				self.docmd(self.__tm.stop, app)
			except ValueError:
				self.help_stop()
		else:
			self.__printerror(self.__MSG_NotConnected)

	def help_stop(self):
		print("Usage: stop {path}")
		print("stop the application at {path}")

	def do_reload(self, args):
		"""reload an application"""
		if self.__tm and self.__tm.hasConnected:
			try:
				app, = args.split()
				self.docmd(self.__tm.reload, app)
			except ValueError:
				self.help_reload()
		else:
			self.__printerror(self.__MSG_NotConnected)

	def help_reload(self):
		print("Usage: reload {path}")
		print("reload the application at {path}")
		
	def do_sessions(self, args):
		"""display the sessions in an application"""
		if self.__tm and self.__tm.hasConnected:
			try:
				app, = args.split()
				sesslist = self.docmd(self.__tm.sessions, app)
				for line in sesslist:
					print(line)
			except TomcatException:
				self.__printexception()
			except ValueError:
				self.help_sessions()
		else:
			self.__printerror(self.__MSG_NotConnected)

	def help_sessions(self):
		print("Usage: sessions {path}")
		print("display the currently active sessions in the application at {path}")

	def do_deploy(self, args):
		if self.__tm and self.__tm.hasConnected:
			args = args.split()
			if len(args) >= 2 and len(args) <= 4:
				path = args[0]
				filename = args[1]
				try:
					update = args[2]
					update = update.lower()
					if update in ("true", "t","y","yes","1"):
						update = True
					elif update in ("false", "f", "n", "no","0"):
						update = False
					else:
						self.help_deploy()
						return
				except IndexError:
					update = None
				try:
					tag = args[3]
				except IndexError:
					tag = None
				fileobj = open(filename, "rb")
				self.docmd(self.__tm.deployWAR, path, fileobj, update, tag)
			else:
				self.help_deploy()
		else:
			self.__printerror(self.__MSG_NotConnected)
	
	def help_deploy(self):
		print("""Usage: deploy {path} {warfile} [update]
deploy a local war file at path
  path    = the path on the server to deploy the application
  warfile = path on the local machine to a war file to deploy
            don't include the 'file:' at the beginning
  update  = optional parameter - default value is false
            use 'true' or 'yes' to undeploy the application
            before deploying it
""")

	def do_undeploy(self, args):
		"""undeploy an application"""
		if self.__tm and self.__tm.hasConnected:
			try:
				app, = args.split()
				self.docmd(self.__tm.undeploy, app)
			except ValueError:
				self.help_undeploy()
		else:
			self.__printerror(self.__MSG_NotConnected)

	def help_undeploy(self):
		print("Usage: undeploy {path}")
		print("undeploy the application at {path}")

	def do_resources(self, args):
		if self.__tm and self.__tm.hasConnected:
			resourcelist = None
			args = args.split()
			if len(args) == 0:
				resourcelist = self.docmd(self.__tm.resources)
			elif len(args) == 1:
				resourcelist = self.docmd(self.__tm.resources,args[0])
			else:
				self.help_resources()
			if resourcelist:
				for line in resourcelist:
					print(line)
		else:
			self.__printerror(self.__MSG_NotConnected)
		
	def help_resources(self):
		print("""Usage: resources [class_name]
list global jndi resources
  class_name  = optional fully qualified Java class name of the resource type you want
""")

	def do_exit(self, args):
		"""exit the interactive manager"""
		print()
		return -1

	def do_quit(self, args):
		"""same as exit"""
		return self.do_exit(args)

	def do_EOF(self, args):
		"""Exit on the end-of-file character"""
		print()
		return self.do_exit(args)
	
	def help_commandline(self):
		print(__doc__)

	def help_license(self):
		print("""
Copyright (c) 2007, Jared Crapo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
""")

	def help_help(self):
		print("get a life")

	def emptyline(self):
		"""Do nothing on an empty line"""
		pass

	def default(self, line):
		print("unknown command: " + line)

	def __printexception(self):
		if self.debugFlag:
			self.__printerror(traceback.format_exc())
		else:
			etype, evalue, etraceback = sys.exc_info()
			self.__printerror(traceback.format_exception_only(etype, evalue))

	def __printerror(self, msg):
		if isinstance(msg, list):
			for line in msg:
				print(line)
		else:
			print(msg)

	def __printstatus(self, msg):
		if self.debugFlag:
			print(msg)


#
# for command line use, we define a nice main routine
def main(argv=None):
	if argv is None:
		argv = sys.argv

	shortopts = "u:p:h"
	longopts = [ "user=", "password=", "debug", "help", "version" ]
	
	# parse command line options
	try:
		try:
			opts, args = getopt.getopt(argv[1:], shortopts, longopts)
		except getopt.error as msg:
			raise Usage(msg)
	
		# process options
		userid = None
		password = None
		command = None
		url = None
		versionFlag = None
		debugFlag = False
		for opt, parm in opts:
			if opt in ("-h", "--help"):
				print(__doc__, file=sys.stderr)
				return 0
			elif opt in ("--version"):
				print("tomcat-manager " + versionString, file=sys.stderr)
				return 0
			elif opt in ("--debug"):
				debugFlag = True
			elif opt in ("-u", "--user"):
				userid = parm
			elif opt in ("-p", "--password"):
				password = parm

		# process arguments
		itm = InteractiveTomcatManager()
		itm.debugFlag = debugFlag
		if args == []:
			itm.cmdloop()
		else:
			url = args[0]
			if password:
				itm.onecmd("connect %s %s %s" % (url, userid, password))
			elif userid:
				itm.onecmd("connect %s %s" % (url, userid))
			else:
				itm.onecmd("connect %s" % url)
			command = ' '.join(args[1:])
			if command:
				itm.onecmd(command)
			else:
				itm.cmdloop()

	except Usage as err:
		print(err.message, file=sys.stderr)
		print("for help use --help", file=sys.stderr)
		return 2


if __name__ == "__main__":
	sys.exit(main())
