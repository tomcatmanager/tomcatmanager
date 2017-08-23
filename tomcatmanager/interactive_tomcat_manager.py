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

import sys
import os
import traceback
import getpass
import cmd2
import xml.dom.minidom
from requests.structures import LookupDict

import tomcatmanager as tm
from .cmd2_config import Cmd2Config


def requires_connection(f):
    """decorator for interactive methods which require a connection"""
    def _requires_connection(self, *args, **kwargs):
        if self.tomcat and self.tomcat.is_connected:
            f(self, *args, **kwargs)
        else:
            # print the message
            self.exit_code = self.exit_codes.error
            self.perr('not connected')
    return _requires_connection


class InteractiveTomcatManager(Cmd2Config, cmd2.Cmd):
    """an interactive command line tool for tomcat manager
    
    each command sets the value of the instance variable exit_code, which follows
    bash behavior for exit codes (available via $?)
    """
    EXIT_CODES = {

        # 'number': 'name'
        0: 'success',
        1: 'error',
        2: 'usage',
      127: 'command_not_found',
    }
    
    # for Cmd2Config
    app_name = 'tomcat-manager'
    app_author = 'tomcatmanager'
    
    # settings for cmd2.Cmd
    prompt = '{}> '.format(app_name)
    cmd2.Cmd.shortcuts.update({'$?': 'exit_code' })

    # our own settings
    exit_codes = LookupDict(name='exit_codes')
    for code, title in EXIT_CODES.items():
        setattr(exit_codes, title, code)

    timeout = 10
    
    
    def __init__(self):
        # initialize Cmd2.Cmd
        unused = ['abbrev', 'continuation_prompt', 'echo']
        for setting in unused:
            try:
                self.settable.pop(setting)
            except:
                pass
        self.settable.update({'editor': 'Program used to edit files'})
        self.settable.update({'timeout': 'Seconds to wait for HTTP connections'})
        cmd2.Cmd.__init__(self)
        self.allow_cli_args = False
        
        # initialize Cmd2Config
        Cmd2Config.__init__(self)

        # prepare our own stuff
        self.tomcat = tm.TomcatManager()
        self.tomcat.timeout = self.timeout
        self.exit_code = None        

    ###
    #
    # Override cmd2.Cmd methods.
    #
    ###
    def emptyline(self):
        """Do nothing on an empty line"""
        pass

    def default(self, line):
        """what to do if we don't recognize the command the user entered"""
        self.exit_code = self.exit_codes.command_not_found
        self.perr('Unknown command: ' + line)

    ###
    #
    # Convenience and shared methods.
    #
    ###
    def pout(self, msg=''):
        """convenience method to print output"""
        print(msg, file=self.stdout)
        
    def perr(self, msg=''):
        """convenience method to print error messages"""
        print(msg, file=sys.stderr)

    def pdebug(self, msg=''):
        """convenience method to print debugging messages"""
        if self.debug:
            print("--" + msg, file=self.stdout)
    
    def pexception(self):
        if self.debug:
            self.perr(traceback.format_exc())
        else:
            etype, evalue, etraceback = sys.exc_info()
            self.perr(traceback.format_exception_only(etype, evalue))   
        
    def docmd(self, func, *args, **kwargs):
        """Call a function and return, printing any exceptions that occur
        
        Sets exit_code to 0 and calls {func}. If func throws a TomcatError,
        set exit_code to 1 and print the exception
        """
        self.exit_code = self.exit_codes.success
        r = func(*args, **kwargs)
        try:
            r.raise_for_status()
        except tm.TomcatError as err:
            self.exit_code = self.exit_codes.failure
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
            self.exit_code = self.exit_codes.success
            return self.docmd(func, path, version)
        else:
            help_func()
            self.exit_code = self.exit_codes.usage

    ###
    #
    # Connecting to Tomcat
    #
    ###
    def do_connect(self, args):
        url = None
        user = None
        password = None
        sargs = args.split()
        
        if len(sargs) == 1:
            # check the configuration file for values
            s = sargs[0]
            if self.config.has_section(s):
                if self.config.has_option(s, 'url'):
                    url = self.config[s]['url']
                if self.config.has_option(s, 'user'):
                    user = self.config[s]['user']
                if self.config.has_option(s, 'password'):
                    password = self.config[s]['password']
            else:
                url = sargs[0]
        elif len(sargs) == 2:
            url = sargs[0]
            user = sargs[1]
        elif len(sargs) == 3:
            url = sargs[0]
            user = sargs[1]
            password = sargs[2]
        else:
            self.help_connect()
            self.exit_code = self.exit_codes.usage
            return
            
        # prompt for password if necessary
        if url and user and not password:
            password = getpass.getpass()

        r = self.tomcat.connect(url, user, password)
        if r.ok:
            self.pdebug('connected to tomcat manager at {}'.format(url))
            self.exit_code = self.exit_codes.success
        else:
            # TODO inspect r to see why we didn't connect so we can provide
            # a useful error message and perhaps exit code
            import pdb
            pdb.set_trace()
            self.perr('tomcat manager not found at {}'.format(url))
            self.exit_code = self.exit_codes.error

    def help_connect(self):
        self.exit_code = self.exit_codes.success
        self.pout("""Usage: connect url [user] [password]
       connect config_name

Connect to a tomcat manager instance.

config_name  A section from the config file. This must contain url, user,
             and password values.

url          The url where the Tomcat Manager web app is located.
user         Optional user to use for authentication.
password     Optional password to use for authentication.

If you specify a user and no password, you will be prompted for the
password. If you don't specify a userid or password, attempt to connect
with no authentication.""")

    @requires_connection
    def do_which(self, args):
        if args:
            self.help_which()
            self.exit_code = self.exit_codes.usage
        else:
            out = 'connected to {}'.format(self.tomcat._url)
            if self.tomcat._user is not None:
                out += ' as {}'.format(self.tomcat._user)
            self.pout(out)
    
    def help_which(self):
        self.exit_code = self.exit_codes.success
        self.pout("""Usage: which

Show the url of the tomcat server you are connected to.""")
        
    ###
    #
    # commands for managing applications
    #
    ###
    def deploy_base(self, args, show_help, update):
        """common method for deploy() and redeploy()"""
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
                self.exit_code = self.exit_codes.success
                self.docmd(self.tomcat.deploy, path, serverwar=warfile,
                        update=update, version=version)
            elif src == local:
                warfile = os.path.expanduser(warfile)
                fileobj = open(warfile, 'rb')
                self.exit_code = self.exit_codes.success
                self.docmd(self.tomcat.deploy, path, localwar=fileobj,
                        update=update, version=version)
            else:
                show_help()
                self.exit_code = self.exit_codes.usage
        else:
            show_help()
            self.exit_code = self.exit_codes.usage

    def deploy_base_help(self):
        """common help string for the deploy() and redeploy()"""
        return """
  server|local  'server' to deploy a war file already on the server
                'local' to transmit a locally available warfile to the server
  warfile       Path to the war file to deploy.

                For 'server', don't include the 'file:' at the beginning,
                and use java style paths (i.e. '/' as path seperator).

                For 'local', give a path according to your local operating
                system conventions.

  path          The path part of the URL where the application will be deployed.
  version       The version string to associate with this deployment."""

    @requires_connection
    def do_deploy(self, args):
        self.deploy_base(args, self.help_deploy, False)

    def help_deploy(self):
        self.exit_code = self.exit_codes.success
        self.pout("""Usage: deploy server|local {warfile} {path} [version]

Install a war file containing a tomcat application in the tomcat server.""")
        self.pout(self.deploy_base_help())

    @requires_connection
    def do_redeploy(self, args):
        self.deploy_base(args, self.help_redeploy, True)

    def help_redeploy(self):
        self.exit_code = self.exit_codes.success
        self.pout("""Usage: redeploy server|local {warfile} {path} [version]

Remove the application currently installed at a given path and install a
new war file there.""")
        self.pout(self.deploy_base_help())

    @requires_connection
    def do_undeploy(self, args):
        args = args.split()
        version = None
        if len(args) in [1, 2]:
            path = args[0]
            if len(args) == 2:
                version = args[1]
            self.exit_code = self.exit_codes.success
            self.docmd(self.tomcat.undeploy, path, version)
        else:
            self.help_undeploy()
            self.exit_code = self.exit_codes.usage

    def help_undeploy(self):
        self.exit_code = self.exit_codes.success
        self.pout("""Usage: undeploy {path} [version]

Remove an application from the tomcat server.

  path     The path part of the URL where the application is deployed.
  version  Optional version string of the application to undeploy. If the
           application was deployed with a version string, it must be
           specified in order to undeploy the application.""")
    
    @requires_connection
    def do_start(self, args):
        self.base_path_version(args, self.tomcat.start, self.help_start)

    def help_start(self):
        self.exit_code = self.exit_codes.success
        self.pout("""Usage: start {path} [version]

Start a tomcat application that has been deployed but isn't running.

  path     The path part of the URL where the application is deployed.
  version  Optional version string of the application to start. If the
           application was deployed with a version string, it must be
           specified in order to start the application.""")

    @requires_connection
    def do_stop(self, args):
        self.base_path_version(args, self.tomcat.stop, self.help_stop)

    def help_stop(self):
        self.exit_code = self.exit_codes.success
        self.pout("""Usage: stop {path} [version]

Stop a tomcat application and leave it deployed on the server.

  path     The path part of the URL where the application is deployed.
  version  Optional version string of the application to stop. If the
           application was deployed with a version string, it must be
           specified in order to stop the application.""")

    @requires_connection
    def do_reload(self, args):
        self.base_path_version(args, self.tomcat.reload, self.help_reload)

    def help_reload(self):
        self.exit_code = self.exit_codes.success
        self.pout("""Usage: reload {path} [version]

Start and stop a tomcat application.

  path     The path part of the URL where the application is deployed.
  version  Optional version string of the application to reload. If the
           application was deployed with a version string, it must be
           specified in order to reload the application.""")

    @requires_connection
    def do_restart(self, args):
        self.do_reload(args)
    
    def help_restart(self):
        self.exit_code = self.exit_codes.success
        self.pout("""Usage: restart {path} [version]

Start and stop a tomcat application. Synonym for reload.

  path     The path part of the URL where the application is deployed.
  version  Optional version string of the application to reload. If the
           application was deployed with a version string, it must be
           specified in order to reload the application.""")
        
    @requires_connection
    def do_sessions(self, args):
        args = args.split()
        version = None
        if len(args) in [1, 2]:
            path = args[0]
            if len(args) == 2:
                version = args[1]
            self.exit_code = self.exit_codes.success
            r = self.docmd(self.tomcat.sessions, path, version)
            if r.ok: self.pout(r.sessions)
        else:
            self.help_sessions()
            self.exit_code = self.exit_codes.usage

    def help_sessions(self):
        self.pout("""Usage: sessions {path} [version]

Show active sessions for a tomcat application.

  path     The path part of the URL where the application is deployed.
  version  Optional version string of the application from which to show
           sessions. If the application was deployed with a version
           string, it must be specified in order to show sessions.""")

    @requires_connection
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
            self.exit_code = self.exit_codes.success
            r = self.docmd(self.tomcat.expire, path, version, idle)
            if r.ok: self.pout(r.sessions)
        else:
            self.help_expire()
            self.exit_code = self.exit_codes.usage

    def help_expire(self):
        self.exit_code = self.exit_codes.success
        self.pout("""Usage: expire {path} [version] {idle}

Expire idle sessions.

  path     The path part of the URL where the application is deployed.
  version  Optional version string of the application from which to
           expire sessions. If the application was deployed with a version
           string, it must be specified in order to expire sessions.
  idle     Expire sessions idle for more than this number of minutes. Use
           0 to expire all sessions.""")

    @requires_connection
    def do_list(self, args):
        if args:
            self.help_list()
            self.exit_code = self.exit_codes.usage
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
        self.exit_code = self.exit_codes.success
        self.pout("""Usage: list

Show all installed applications.""")

    ###
    #
    # These commands that don't affect change, they just return some
    # information from the server.
    #
    ###
    @requires_connection
    def do_serverinfo(self, args):
        if args:
            self.help_serverinfo()
            self.exit_code = self.exit_codes.usage
        else:
            r = self.docmd(self.tomcat.server_info)
            self.pout(r.result)

    def help_serverinfo(self):
        self.exit_code = self.exit_codes.success
        self.pout("""Usage: serverinfo

Show information about the server.""")

    @requires_connection
    def do_status(self, args):
        if args:
            self.help_status()
            self.exit_code = self.exit_codes.usage
        else:
            r = self.docmd(self.tomcat.status_xml)
            root = xml.dom.minidom.parseString(r.status_xml)
            self.pout(root.toprettyxml(indent='   '))

    def help_status(self):
        self.exit_code = self.exit_codes.success
        self.pout("""Usage: status

Show server status information in xml format.""")

    @requires_connection
    def do_vminfo(self, args):
        if args:
            self.help_vminfo()
            self.exit_code = self.exit_codes.usage
        else:
            response = self.docmd(self.tomcat.vm_info)
            self.pout(response.vm_info)

    def help_vminfo(self):
        self.exit_code = self.exit_codes.success
        self.pout("""Usage: vminfo

Show diagnostic information about the jvm.""")

    @requires_connection
    def do_sslconnectorciphers(self, args):
        if args:
            self.help_sslconnectorciphers()
            self.exit_code = self.exit_codes.usage
        else:
            response = self.docmd(self.tomcat.ssl_connector_ciphers)
            self.pout(response.ssl_connector_ciphers)
    
    def help_sslconnectorciphers(self):
        self.exit_code = self.exit_codes.success
        self.pout("""Usage: sslconnectorciphers

Show SSL/TLS ciphers configured for each connector.""")

    @requires_connection
    def do_threaddump(self, args):
        if args:
            self.help_threaddump()
            self.exit_code = self.exit_codes.usage
        else:
            response = self.docmd(self.tomcat.thread_dump)
            self.pout(response.thread_dump)

    def help_threaddump(self):
        self.exit_code = self.exit_codes.success
        self.pout("""Usage: threaddump

Show a jvm thread dump.""")

    @requires_connection
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
            self.exit_code = self.exit_codes.usage

    def help_resources(self):
        self.exit_code = self.exit_codes.success
        self.pout("""Usage: resources [class_name]

Show global jndi resources configured in tomcat.

class_name  Optional fully qualified java class name of the resource type
            to show.""")

    @requires_connection
    def do_findleakers(self, args):
        if args:
            self.help_findleakers()
            self.exit_code = self.exit_codes.usage
        else:
            response = self.docmd(self.tomcat.find_leakers)
            for leaker in response.leakers:
                self.pout(leaker)
    
    def help_findleakers(self):
        self.exit_code = self.exit_codes.success
        self.pout("""Usage: findleakers

Show tomcat applications that leak memory.

WARNING: this triggers a full garbage collection on the server. Use with
extreme caution on production systems.""")

    ###
    #
    # miscellaneous user accessible commands
    #
    ###
    def do_exit(self, args):
        """exit the interactive manager"""
        self.exit_code = self.exit_codes.success
        return self._STOP_AND_EXIT

    def do_quit(self, args):
        """same as exit"""
        return self.do_exit(args)

    def do_eof(self, args):
        """Exit on the end-of-file character"""
        return self.do_exit(args)

    def do_version(self, args):
        self.exit_code = self.exit_codes.success
        self.pout('{} {} (works with Tomcat >= 7.0 and <= 8.5)'.format(self.app_name, tm.__version__))
    
    def help_version(self):
        self.exit_code = self.exit_codes.success
        self.pout("""Usage: version
        
Show version information.""")
    
    def do_exit_code(self, args):
        """show the value of the exit_code variable"""
        # don't set the exit code here, just show it
        self.pout(self.exit_code)

    def help_exit_code(self):
        self.exit_code = self.exit_codes.success
        self.pout("""Usage: exit_code
        
Show the value of the exit_code variable, similar to $? in ksh/bash""")

    def do_license(self, args):
        self.exit_code = self.exit_codes.success
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
        self.exit_code = self.exit_codes.success
        self.pout("""Usage: license
        
Show license information.""")

