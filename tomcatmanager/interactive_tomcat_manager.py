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


	tomcat-manager --user=userid, --password=mypass [--debug] manager_url

		connect to the tomcat manager at manager_url, using userid and
		mypass for authentication, and then enter the interactive shell


	Once you are in the interactive shell, type "help" for a list of
	commands and their arguments.
	
	To view the license for this software, enter the interactive shell
	and type "license"


Options
-------

	--user, -u        the user to use for authentication
	                  with the tomcat application

	--password, -p    the password to use for authentication
	                  with the tomcat application
	
	--debug           show additional debugging information
	
	--version         show the version information and exit
	
	--help, -h        show command line usage
"""
import argparse
import sys
import traceback
import getpass
import urllib.request
import tomcatmanager as tm

# use cmd2 if it's available
try:
	import cmd2 as cmd
except ImportError as e:
	import cmd

#
#
version_number='8.5'
prog_name='tomcat-manager'
version_string='%s %s (works with Tomcat Manager <= 8.5)' % (prog_name, version_number)


class InteractiveTomcatManager(cmd.Cmd):
	"""an interactive command line tool for tomcat manager
	
	each command sets the value of the instance variable exit_code, which follows
	shell rules for exit_codes:
	
	0 - completed successfully
	1 - error
	2 - improper usage
	"""
	def __init__(self):
		super().__init__()
		self.prompt = prog_name + '>'
		self.tomcat_manager = None
		self.__MSG_not_connected = 'not connected'
		self.debug_flag = False
		self.exit_code = None
		# only relevant for cmd2, but doesn't hurt anything on cmd
		self.allow_cli_args = False
		

	def pout(self, msg):
		"""convenience method to print output"""
		if isinstance(msg, list):
			for line in msg:
				print(line.rstrip(), file=self.stdout)
		else:
			print(msg, file=self.stdout)
		
	def perr(self, msg):
		"""convenience method to print error messages"""
		if isinstance(msg, list):
			for line in msg:
				print(line.rstrip(), file=sys.stderr)
		else:
			print(msg, file=sys.stderr)

	def pdebug(self, msg):
		"""convenience method to print debugging messages"""
		if self.debug_flag:
			if isinstance(msg, list):
				for line in msg:
					print("--" + line.rstrip(), file=self.stdout)
			else:
				print("--" + msg, file=self.stdout)
	
	def pexception(self):
		if self.debug_flag:
			self.perr(traceback.format_exc())
		else:
			etype, evalue, etraceback = sys.exc_info()
			self.perr(traceback.format_exception_only(etype, evalue))	
	
	def docmd(self, func, *args):
		"""call a function and return, printing any exceptions that occur
		
		You should set exit_code to 0 before calling this, assuming it completes
		successfully. If it doesn't complete successfully, this will set exit_code
		to 1.
		"""
		try:
			return func(*args)
		except tm.TomcatException:
			self.exit_code = 1
			self.pexception()

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

			self.tomcat_manager = tm.TomcatManager(url, username, password)
			apps = self.tomcat_manager.list()
			self.pdebug("connected to tomcat manager at %s" % url)
			self.exit_code = 0
		except ValueError:
			self.help_connect()
			self.exit_code = 2
		except urllib.request.HTTPError as e:
			self.exit_code = 1
			if e.code == 401:
				self.perr("login failed")
			elif e.code == 403:
				self.perr("login failed")
			elif e.code == 404:
				self.perr("tomcat manager not found at %s" % url)
			else:
				self.pexception()

	def help_connect(self):
		self.exit_code = 0
		self.pout("usage: connect url [username] [password]")
		self.pout("connect to a tomcat manager instance")
		self.pout("if you specify a username and no password, you will be prompted for the password")
		self.pout("if you don't specify a username or password, connect with no authentication")

	def do_serverinfo(self, args):
		if args:
			self.help_serverinfo()
			self.exit_code = 2
		elif self.tomcat_manager and self.tomcat_manager.has_connected:
			self.exit_code = 0
			info = self.docmd(self.tomcat_manager.serverinfo)
			for key,value in iter(sorted(info.items())):
				self.pout("%s: %s" % (key, value))
		else:
			self.exit_code = 1
			self.perr(self.__MSG_not_connected)
	
	def help_serverinfo(self):
		self.exit_code = 0
		self.pout("usage: serverinfo")
		self.pout("show information about the server")

	def do_vminfo(self, args):
		if args:
			self.help_vminfo()
			self.exit_code = 2
		elif self.tomcat_manager and self.tomcat_manager.has_connected:
			self.exit_code = 0
			info = self.docmd(self.tomcat_manager.vminfo)
			self.pout(info)
		else:
			self.exit_code = 1
			self.perr(self.__MSG_not_connected)	
	
	def help_vminfo(self):
		self.exit_code = 0
		self.pout("Usage: vminfo")
		self.pout("show information about the jvm")

	def do_sslconnectorciphers(self, args):
		if args:
			self.help_sslconnectorciphers()
			self.exit_code = 2
		elif self.tomcat_manager and self.tomcat_manager.has_connected:
			self.exit_code = 0
			info = self.docmd(self.tomcat_manager.sslConnectorCiphers)
			self.pout(info)
		else:
			self.exit_code = 1
			self.perr(self.__MSG_not_connected)	
	
	def help_sslconnectorciphers(self):
		self.exit_code = 0
		self.pout("Usage: sslconnectorciphers")
		self.pout("show SSL/TLS ciphers configured for each connector")

	def do_threaddump(self, args):
		if args:
			self.help_threaddump()
			self.exit_code = 2
		elif self.tomcat_manager and self.tomcat_manager.has_connected:
			self.exit_code = 0
			info = self.docmd(self.tomcat_manager.threaddump)
			self.pout(info)
		else:
			self.exit_code = 1
			self.perr(self.__MSG_not_connected)	
	
	def help_threaddump(self):
		self.exit_code = 0
		self.pout("Usage: threaddump")
		self.pout("show a jvm thread dump")

	def do_findleaks(self, args):
		if args:
			self.help_findleaks()
			self.exit_code = 2
		elif self.tomcat_manager and self.tomcat_manager.has_connected:
			self.exit_code = 0
			info = self.docmd(self.tomcat_manager.findleaks)
			self.pout(info)
		else:
			self.exit_code = 1
			self.perr(self.__MSG_not_connected)	
	
	def help_findleaks(self):
		self.exit_code = 0
		self.pout("Usage: findleaks")
		self.pout("find apps that leak memory")
		self.pout("")
		self.pout("CAUTION: this triggers a full garbage collection on the server")
		self.pout("Use with extreme caution on production systems")

	def do_status(self, args):
		if args:
			self.help_status()
			self.exit_code = 2
		elif self.tomcat_manager and self.tomcat_manager.has_connected:
			self.exit_code = 0
			info = self.docmd(self.tomcat_manager.status)
			self.pout(info)
		else:
			self.exit_code = 1
			self.perr(self.__MSG_not_connected)	
	
	def help_status(self):
		self.exit_code = 0
		self.pout("Usage: status")
		self.pout("get server status information in XML format")

	def do_list(self, args):
		"""list the applications on the server"""
		if args:
			self.help_list()
			self.exit_code = 2
		elif self.tomcat_manager and self.tomcat_manager.has_connected:
			apps = self.docmd(self.tomcat_manager.list)
			cw = [24, 7, 8, 36]
			# build the format string from the column widths so we only
			# have the column widths hardcoded in one place
			fmt = " ".join(list(map(lambda x: "%"+str(x)+"s",cw)))
			dashes = "-"*80
			self.pout( fmt % ("Path".ljust(cw[0]), "Status".ljust(cw[1]), "Sessions".rjust(cw[2]), "Directory".ljust(cw[3])) )
			self.pout( fmt % (dashes[:cw[0]], dashes[:cw[1]], dashes[:cw[2]], dashes[:cw[3]]) )
			for app in apps:
				path, status, session, directory = app[:4]
				self.pout( fmt % (app[0].ljust(cw[0]), app[1].ljust(cw[1]), app[2].rjust(cw[2]), app[3].ljust(cw[3])) )
		else:
			self.exit_code = 1
			self.perr(self.__MSG_not_connected)

	def help_list(self):
		self.exit_code = 0
		self.pout("Usage: list")
		self.pout("list installed applications")

	def do_start(self, args):
		"""start an application"""
		if self.tomcat_manager and self.tomcat_manager.has_connected:
			try:
				app, = args.split()
				self.exit_code = 0
				self.docmd(self.tomcat_manager.start, app)
			except ValueError:
				self.help_start()
				self.exit_code = 2
		else:
			self.exit_code = 1
			self.perr(self.__MSG_not_connected)

	def help_start(self):
		self.exit_code = 0
		self.pout("Usage: start {path}")
		self.pout("start the application at {path}")

	def do_stop(self, args):
		"""stop an application"""
		if self.tomcat_manager and self.tomcat_manager.has_connected:
			try:
				app, = args.split()
				self.exit_code = 0
				self.docmd(self.tomcat_manager.stop, app)
			except ValueError:
				self.help_stop()
				self.exit_code = 2
		else:
			self.exit_code = 1
			self.perr(self.__MSG_not_connected)

	def help_stop(self):
		self.exit_code = 0
		self.pout("Usage: stop {path}")
		self.pout("stop the application at {path}")

	def do_reload(self, args):
		"""reload an application"""
		if self.tomcat_manager and self.tomcat_manager.has_connected:
			try:
				app, = args.split()
				self.exit_code = 0
				self.docmd(self.tomcat_manager.reload, app)
			except ValueError:
				self.help_reload()
				self.exit_code = 2
		else:
			self.exit_code = 1
			self.perr(self.__MSG_not_connected)

	def help_reload(self):
		self.exit_code = 0
		self.pout("Usage: reload {path}")
		self.pout("reload the application at {path}")
		
	def do_sessions(self, args):
		"""display the sessions in an application"""
		if self.tomcat_manager and self.tomcat_manager.has_connected:
			try:
				app, = args.split()
				self.exit_code = 0
				sesslist = self.docmd(self.tomcat_manager.sessions, app)
				self.pout(sesslist)
			except ValueError:
				self.help_sessions()
				self.exit_code = 2
		else:
			self.exit_code = 1
			self.perr(self.__MSG_not_connected)

	def help_sessions(self):
		self.pout("Usage: sessions {path}")
		self.pout("display the currently active sessions in the application at {path}")

	def do_expire(self, args):
		"""expire sessions idle for longer than idle minutes"""
		if self.tomcat_manager and self.tomcat_manager.has_connected:
			try:
				app,idle, = args.split()
				self.exit_code = 0
				sesslist = self.docmd(self.tomcat_manager.expire, app, idle)
				self.pout(sesslist)
			except ValueError:
				self.help_expire()
				self.exit_code = 2
		else:
			self.exit_code = 1
			self.perr(self.__MSG_not_connected)

	def help_expire(self):
		self.exit_code = 0
		self.pout("Usage: expire {path} {idle}")
		self.pout("expire sessions idle for more than {idle} minutes in the application at {path}")

	def do_deploy(self, args):
		if self.tomcat_manager and self.tomcat_manager.has_connected:
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
						self.exit_code = 2
						return
				except IndexError:
					update = None

				try:
					tag = args[3]
				except IndexError:
					tag = None

				fileobj = open(filename, "rb")
				self.exit_code = 0
				self.docmd(self.tomcat_manager.deployWAR, path, fileobj, update, tag)
			else:
				self.help_deploy()
				self.exit_code = 2
		else:
			self.exit_code = 1
			self.perr(self.__MSG_not_connected)
	
	def help_deploy(self):
		self.exit_code = 0
		self.pout("""Usage: deploy {path} {warfile} [update]
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
		if self.tomcat_manager and self.tomcat_manager.has_connected:
			try:
				app, = args.split()
				self.exit_code = 0
				self.docmd(self.tomcat_manager.undeploy, app)
			except ValueError:
				self.help_undeploy()
				self.exit_code = 2
		else:
			self.exit_code = 1
			self.perr(self.__MSG_not_connected)

	def help_undeploy(self):
		self.exit_code = 0
		self.pout("Usage: undeploy {path}")
		self.pout("undeploy the application at {path}")

	def do_resources(self, args):
		if self.tomcat_manager and self.tomcat_manager.has_connected:
			resourcelist = None
			args = args.split()
			self.exit_code = 0
			if len(args) == 0:
				resourcelist = self.docmd(self.tomcat_manager.resources)
			elif len(args) == 1:
				resourcelist = self.docmd(self.tomcat_manager.resources, args[0])
			else:
				self.help_resources()
				self.exit_code = 2
			if resourcelist:
				self.pout(resourcelist)
		else:
			self.exit_code = 1
			self.perr(self.__MSG_not_connected)
		
	def help_resources(self):
		self.exit_code = 0
		self.pout("""Usage: resources [class_name]
list global jndi resources
  class_name  = optional fully qualified Java class name of the resource type you want
""")

	def do_version(self, args):
		self.exit_code = 0
		self.pout(version_string)
	
	def help_version(self):
		self.exit_code = 0
		self.pout('show version information')

	def do_exit(self, args):
		"""exit the interactive manager"""
		self.exit_code = 0
		return True

	def do_quit(self, args):
		"""same as exit"""
		return self.do_exit(args)

	def do_EOF(self, args):
		"""Exit on the end-of-file character"""
		return self.do_exit(args)
	
	def do_exit_code(self, args):
		"""show the value of the exit_code variable"""
		# don't set the exit code here, just show it
		self.pout(self.exit_code)

	def help_exit_code(self):
		self.exit_code = 0
		self.pout('show the value of the exit_code variable, similar to $? in sh/ksh/bash')
				
	def help_commandline(self):
		self.exit_code = 0
		self.pout(__doc__)

	def do_license(self, args):
		self.exit_code = 0
		self.pout("""
Copyright (c) 2007 Jared Crapo

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

	def help_license(self):
		self.exit_code = 0
		self.pout("show license information")

	def help_help(self):
		self.exit_code = 0
		self.pout('here\'s a dollar, you\'ll have to buy a clue elsewhere')

	def emptyline(self):
		"""Do nothing on an empty line"""
		pass

	def default(self, line):
		self.exit_code = 2
		self.perr('unknown command: ' + line)
