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
import os
import traceback
import getpass
import cmd2
import urllib.request

import tomcatmanager as tm


#
#
version_number='8.5'
prog_name='tomcat-manager'
version_string='%s %s (works with Tomcat Manager <= 8.5)' % (prog_name, version_number)


class InteractiveTomcatManager(cmd2.Cmd):
	"""an interactive command line tool for tomcat manager
	
	each command sets the value of the instance variable exit_code, which follows
	bash behavior for exit codes (available via $?):
	
	0 - completed successfully
	1 - error
	2 - improper usage
	127 - unknown command
	"""

	# override behavior of cmd2.Cmd
	cmd2.Cmd.shortcuts.update({'$?': 'exit_code' })
	
	def __init__(self):
		super().__init__()

		self.tomcat = None
		self.debug_flag = False
		self.exit_code = None

		# this is the list of commands that require us to be connected
		# to a tomcat server
		# postparsing_precmd() checks the list and handles everything appropriately
		self.connected_commands = [
			# info commands
			'list', 'serverinfo', 'status', 'vminfo',
			'sslconnectorciphers', 'threaddump', 'resources',
			'findleakers', 'sessions',
			# action commands
			'expire', 'start', 'stop', 'reload',
			'deploy', 'redeploy', 'undeploy',
			]
		
		# settings for cmd2.Cmd
		self.prompt = prog_name + '>'
		self.allow_cli_args = False

	###
	#
	# override cmd2.Cmd methods
	#
	###
	def postparsing_precmd(self, statement):
		"""This runs after parsing the command-line, but before anything else; even before adding cmd to history.
		
		We use it to fail commands that require a connection if we aren't connected
		
		Even if we fail the command for not being connected we add it to history
		"""
		stop = False
		if statement.parsed.command in self.connected_commands:
			if self.tomcat and self.tomcat.is_connected:
				# everything is fine, just run the statement as is
				return stop, statement
			else:
				# we aren't connected and the command requires it
				# add it to history		
				# this is verbatim from cmd2.Cmd.onecmd_plus_hooks()
				if statement.parsed.command not in self.excludeFromHistory:
					self.history.append(statement.parsed.raw)
			
				# print the message
				self.exit_code = 1
				self.perr('not connected')
			
				# tell our super to not do anything
				raise cmd2.EmptyStatement
		else:
			# this command doesn't require us to be connected, run it as is
			return stop, statement

	def emptyline(self):
		"""Do nothing on an empty line"""
		pass

	def default(self, line):
		"""what to do if we don't recognize the command the user entered"""
		self.exit_code = 127
		self.perr('unknown command: ' + line)

	###
	#
	# convenience and shared methods
	#
	###
	def pout(self, msg=''):
		"""convenience method to print output"""
		if isinstance(msg, list):
			for line in msg:
				print(line.rstrip(), file=self.stdout)
		else:
			print(msg, file=self.stdout)
		
	def perr(self, msg=''):
		"""convenience method to print error messages"""
		if isinstance(msg, list):
			for line in msg:
				print(line.rstrip(), file=sys.stderr)
		else:
			print(msg, file=sys.stderr)

	def pdebug(self, msg=''):
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
		
	def docmd(self, func, *args, **kwargs):
		"""Call a function and return, printing any exceptions that occur
		
		Sets exit_code to 0 and calls {func}. If func throws a TomcatError,
		set exit_code to 1 and print the exception
		"""
		self.exit_code = 0
		r = func(*args, **kwargs)
		try:
			r.raise_for_status()
		except tm.TomcatError as err:
			self.exit_code = 1
			self.perr(str(err))
		return r

	def base_path_version(self, args, func, help_func):
		"""do any command that takes a path and an optional version"""
		args = args.split()
		version = None
		if len(args) in [1, 2]:
			path = args[0]
			if len(args) == 2:
				version = args[1]
			self.exit_code = 0
			return self.docmd(func, path, version)
		else:
			help_func()
			self.exit_code = 2

	def deploy_base_help(self):
		"""common help string for the various flavors of deploy commands"""
		return """
  server|local  'server' to deploy a war file already on the server
                'local' to transmit a locally available warfile to the server
  warfile       Path to the war file to deploy.

                For 'server', don't include the 'file:' at the beginning,
                and use java style paths (i.e. '/' as path seperator).

                For 'local', give a path according to your local operating
                system conventions.

  path          The path part of the URL where the application will be deployed.
  version       The version to associate with this deployment."""

	###
	#
	# methods for commands exposed to the user
	#
	###
	def do_exit(self, args):
		"""exit the interactive manager"""
		self.exit_code = 0
		return self._STOP_AND_EXIT

	def do_quit(self, args):
		"""same as exit"""
		return self.do_exit(args)

	def do_eof(self, args):
		"""Exit on the end-of-file character"""
		return self.do_exit(args)

	def do_connect(self, args):
		"""connect to an instance of the tomcat manager application"""
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

			self.tomcat = tm.TomcatManager(url, username, password)
			if self.tomcat.is_connected:
				self.pdebug('connected to tomcat manager at {}'.format(url))
				self.exit_code = 0
			else:
				self.perr('tomcat manager not found at {}'.format(url))
				self.exit_code = 1
		except ValueError:
			self.help_connect()
			self.exit_code = 2

	def help_connect(self):
		self.exit_code = 0
		self.pout('usage: connect url [username] [password]')
		self.pout('connect to a tomcat manager instance')
		self.pout('if you specify a username and no password, you will be prompted for the password')
		self.pout('if you don\'t specify a username or password, connect with no authentication')

	###
	#
	# the info commands exposed to the user, i.e. commands that don't really do
	# anything, they just return some information from the server
	#
	###
	def do_list(self, args):
		"""list the applications on the server"""
		if args:
			self.help_list()
			self.exit_code = 2
		else:
			response = self.docmd(self.tomcat.list)
			fmt = '{:24.24} {:7.7} {:>8.8} {:36.36}'
			dashes = '-'*80
			self.pout(fmt.format('Path', 'Status', 'Sessions', 'Directory'))
			self.pout(fmt.format(dashes, dashes, dashes, dashes))
			for app in response.apps:
				path, status, session, directory = app[:4]
				self.pout(fmt.format(path, status, session, directory))

	def help_list(self):
		self.exit_code = 0
		self.pout('Usage: list')
		self.pout('list installed applications')

	def do_serverinfo(self, args):
		if args:
			self.help_serverinfo()
			self.exit_code = 2
		else:
			r = self.docmd(self.tomcat.server_info)
			self.pout(r.result)

	def help_serverinfo(self):
		self.exit_code = 0
		self.pout('usage: serverinfo')
		self.pout('show information about the server')

	def do_status(self, args):
		if args:
			self.help_status()
			self.exit_code = 2
		else:
			response = self.docmd(self.tomcat.status_xml)
			self.pout(response.status_xml)

	def help_status(self):
		self.exit_code = 0
		self.pout('Usage: status')
		self.pout('get server status information in XML format')

	def do_vminfo(self, args):
		if args:
			self.help_vminfo()
			self.exit_code = 2
		else:
			response = self.docmd(self.tomcat.vm_info)
			self.pout(response.vm_info)

	def help_vminfo(self):
		self.exit_code = 0
		self.pout('Usage: vminfo')
		self.pout('show information about the jvm')

	def do_sslconnectorciphers(self, args):
		if args:
			self.help_sslconnectorciphers()
			self.exit_code = 2
		else:
			response = self.docmd(self.tomcat.ssl_connector_ciphers)
			self.pout(response.ssl_connector_ciphers)
	
	def help_sslconnectorciphers(self):
		self.exit_code = 0
		self.pout('Usage: sslconnectorciphers')
		self.pout('show SSL/TLS ciphers configured for each connector')

	def do_threaddump(self, args):
		if args:
			self.help_threaddump()
			self.exit_code = 2
		else:
			response = self.docmd(self.tomcat.thread_dump)
			self.pout(response.thread_dump)

	def help_threaddump(self):
		self.exit_code = 0
		self.pout('Usage: threaddump')
		self.pout('show a jvm thread dump')

	def do_resources(self, args):
		if len(args.split()) in [0,1]:
			try:
				# this nifty line barfs if there are other than 1 argument
				type, = args.split()
			except ValueError:
				type = None
			r = self.docmd(self.tomcat.resources, type)
			for resource, classname in iter(sorted(r.resources.items())):
				self.pout('{}: {}'.format(resource, classname))
		else:
			self.help_resources()
			self.exit_code = 2

	def help_resources(self):
		self.exit_code = 0
		self.pout('Usage: resources [class_name]')
		self.pout('list global jndi resources')
		self.pout('  class_name  = optional fully qualified Java class name of the resource type you want')

	def do_findleakers(self, args):
		if args:
			self.help_findleakers()
			self.exit_code = 2
		else:
			response = self.docmd(self.tomcat.find_leakers)
			self.pout(response.leakers)
	
	def help_findleakers(self):
		self.exit_code = 0
		self.pout('Usage: findleakers')
		self.pout('find apps that leak memory')
		self.pout()
		self.pout('CAUTION: this triggers a full garbage collection on the server')
		self.pout('Use with extreme caution on production systems')

	def do_sessions(self, args):
		args = args.split()
		version = None
		if len(args) in [1, 2]:
			path = args[0]
			if len(args) == 2:
				version = args[1]
			self.exit_code = 0
			r = self.docmd(self.tomcat.sessions, path, version)
			if r.ok: self.pout(r.sessions)
		else:
			self.help_sessions()
			self.exit_code = 2

	def help_sessions(self):
		self.pout("""Usage: sessions {path} [version]

Display number of active sessions.

  path     The path part of the URL where the application is deployed.
  version  Optional version of the application from which to expire
           sessions. If the application was deployed with a version, the
           version must be specified in order to expire sessions in it.""")

	###
	#
	# the action commands exposed to the user, i.e. commands that actually effect
	# some change on the server
	#
	###
	def do_expire(self, args):
		args = args.split()
		version = None
		if len(args) in [2, 3]:
			path = args[0]
			if len(args) == 2:
				idle = args[1]
			else:
				version = args[1]
				idle = args[2]
			self.exit_code = 0
			r = self.docmd(self.tomcat.expire, path, version, idle)
			if r.ok: self.pout(r.sessions)
		else:
			self.help_expire()
			self.exit_code = 2

	def help_expire(self):
		self.exit_code = 0
		self.pout("""Usage: expire {path} [version] {idle}

Expire idle sessions.

  path     The path part of the URL where the application is deployed.
  version  Optional version of the application from which to expire
           sessions. If the application was deployed with a version, the
           version must be specified in order to expire sessions in it.
  idle     Sessions idle for more than this number of minutes are expired.
           Use 0 to expire all sessions.""")

	def do_start(self, args):
		self.base_path_version(args, self.tomcat.start, self.help_start)

	def help_start(self):
		self.exit_code = 0
		self.pout("""Usage: start {path} [version]

Start a tomcat application.

  path     The path part of the URL where the application is deployed.
  version  Optional version of the application to start. If the
           application was deployed with a version, the version must be
           specified in order to start it.""")

	def do_stop(self, args):
		self.base_path_version(args, self.tomcat.stop, self.help_stop)

	def help_stop(self):
		self.exit_code = 0
		self.pout("""Usage: stop {path} [version]

Stop a tomcat application.

  path     The path part of the URL where the application is deployed.
  version  Optional version of the application to stop. If the
           application was deployed with a version, the version must be
           specified in order to stop it.""")

	def do_reload(self, args):
		self.base_path_version(args, self.tomcat.reload, self.help_reload)

	def help_reload(self):
		self.exit_code = 0
		self.pout("""Usage: reload {path} [version]

Reload a tomcat application.

  path     The path part of the URL where the application is deployed.
  version  Optional version of the application to reload. If the
           application was deployed with a version, the version must be
           specified in order to reload it.""")

	def deploy_base(self, args, show_help, update):
		server = 'server'
		local = 'local'
		args = args.split()
		if len(args) in [3, 4]:
			src = args[0]
			warfile = args[1]
			path = args[2]
			version = None
			if len(args) == 4:
				version = args[3]

			if server.startswith(src): src = server
			if local.startswith(src): src = local
			
			if src == server:
				self.exit_code = 0
				self.docmd(self.tomcat.deploy, path, serverwar=warfile,
						update=update, version=version)
			elif src == local:
				warfile = os.path.expanduser(warfile)
				fileobj = open(warfile, 'rb')
				self.exit_code = 0
				self.docmd(self.tomcat.deploy, path, localwar=fileobj,
						update=update, version=version)
			else:
				show_help()
				self.exit_code = 2
		else:
			show_help()
			self.exit_code = 2

	def do_deploy(self, args):
		self.deploy_base(args, self.help_deploy, False)

	def help_deploy(self):
		self.exit_code = 0
		self.pout("""Usage: deploy server|local {warfile} {path} [version]

Deploy a tomcat application contained in a war file.""")
		self.pout(self.deploy_base_help())

	def do_redeploy(self, args):
		self.deploy_base(args, self.help_redeploy, True)

	def help_redeploy(self):
		self.exit_code = 0
		self.pout("""Usage: redeploy server|local {warfile} {path} [version]

Redeploy a tomcat application contained in a war file by undeploying the
application located at {path} and then deploying {warfile}.""")
		self.pout(self.deploy_base_help())

	def do_undeploy(self, args):
		args = args.split()
		version = None
		if len(args) in [1, 2]:
			path = args[0]
			if len(args) == 2:
				version = args[1]
			self.exit_code = 0
			self.docmd(self.tomcat.undeploy, path, version)
		else:
			self.help_undeploy()
			self.exit_code = 2

	def help_undeploy(self):
		self.exit_code = 0
		self.pout("""Usage: undeploy {path} [version]

Undeploy a tomcat application.

  path     The path part of the URL where the application is deployed.
  version  Version of the application to undeploy. If the application was
           deployed with a version, a version must be specified to undeploy it.""")

	###
	#
	# miscellaneous user accessible commands
	#
	###
	def do_version(self, args):
		self.exit_code = 0
		self.pout(version_string)
	
	def help_version(self):
		self.exit_code = 0
		self.pout('show version information')
	
	def do_exit_code(self, args):
		"""show the value of the exit_code variable"""
		# don't set the exit code here, just show it
		self.pout(self.exit_code)

	def help_exit_code(self):
		self.exit_code = 0
		self.pout('show the value of the exit_code variable, similar to $? in ksh/bash')
				
	def help_commandline(self):
		self.exit_code = 0
		self.pout(__doc__)

	def do_license(self, args):
		self.exit_code = 0
		self.pout("""
Copyright 2007 Jared Crapo

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
		self.pout('show license information')

	def help_help(self):
		self.exit_code = 0
		self.pout('here\'s a dollar, you\'ll have to buy a clue elsewhere')