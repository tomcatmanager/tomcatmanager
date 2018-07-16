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
"""
Classes and functions for the 'tomcat-manager' command line program.
"""

import argparse
import ast
import configparser
import getpass
import os
import sys
import traceback
import xml.dom.minidom
from http.client import responses
from typing import Callable, Any, List

import appdirs
from attrdict import AttrDict
import requests
import cmd2

import tomcatmanager as tm


def requires_connection(func: Callable) -> Callable:
    """Decorator for interactive methods which require a connection."""
    def _requires_connection(self, *args, **kwargs):
        if self.tomcat and self.tomcat.is_connected:
            func(self, *args, **kwargs)
        else:
            # print the message
            self.exit_code = self.exit_codes.error
            self.perror('not connected')
    _requires_connection.__doc__ = func.__doc__
    return _requires_connection

def _path_version_parser(cmdname: str,
                         helpmsg: str
                        ) -> argparse.ArgumentParser:
    """Construct an argparser using the given parameters"""
    parser = argparse.ArgumentParser(prog=cmdname, description=helpmsg)
    parser.add_argument(
        '-v',
        '--version',
        help="""Optional version string of the application to
             {cmdname}. If the application was deployed with
             a version string, it must be specified in order to
             {cmdname} the application.""".format(cmdname=cmdname)
    )
    path_help = 'The path part of the URL where the application is deployed.'
    parser.add_argument('path', help=path_help)
    return parser

def _deploy_parser(name: str,
                   desc: str,
                   localfunc: Callable,
                   serverfunc: Callable,
                   contextfunc: Callable
                  ) -> argparse.ArgumentParser:
    """Construct a argument parser for the deploy or redeploy commands."""
    deploy_parser = argparse.ArgumentParser(
        prog=name,
        description=desc,
    )
    deploy_subparsers = deploy_parser.add_subparsers(title='methods', dest='method')
    # local subparser
    deploy_local_parser = deploy_subparsers.add_parser(
        'local',
        description='transmit a locally available warfile to the server',
        help='transmit a locally available warfile to the server',
    )
    deploy_local_parser.add_argument(
        '-v', '--version',
        help='version string to associate with this deployment'
    )
    deploy_local_parser.add_argument('warfile')
    deploy_local_parser.add_argument('path')
    deploy_local_parser.set_defaults(func=localfunc)
    # server subparser
    deploy_server_parser = deploy_subparsers.add_parser(
        'server',
        description='deploy a warfile already on the server',
        help='deploy a warfile already on the server'
    )
    deploy_server_parser.add_argument(
        '-v', '--version',
        help='version string to associate with this deployment'
    )
    deploy_server_parser.add_argument('warfile')
    deploy_server_parser.add_argument('path')
    deploy_server_parser.set_defaults(func=serverfunc)
    # context subparser
    deploy_context_parser = deploy_subparsers.add_parser(
        'context',
        description='deploy a contextfile already on the server',
        help='deploy a contextfile already on the server',
    )
    deploy_context_parser.add_argument(
        '-v', '--version',
        help='version string to associate with this deployment',
    )
    deploy_context_parser.add_argument('contextfile')
    deploy_context_parser.add_argument('warfile', nargs='?')
    deploy_context_parser.add_argument('path')
    deploy_context_parser.set_defaults(func=contextfunc)
    return deploy_parser

# pylint: disable=too-many-public-methods
class InteractiveTomcatManager(cmd2.Cmd):
    """An interactive command line tool for the Tomcat Manager web application.

    each command sets the value of the instance variable exit_code,
    which mirrors bash standard values for exit codes (available via $?)
    """

    EXIT_CODES = {
        # 'number': 'name'
        0: 'success',
        1: 'error',
        2: 'usage',
        127: 'command_not_found',
    }

    # Possible boolean values
    BOOLEAN_VALUES = {'1': True, 'yes': True, 'y': True, 'true': True,
                      't': True, 'on': True,
                      '0': False, 'no': False, 'n': False,
                      'false': False, 'f': False, 'off': False}

    exit_codes = AttrDict()
    for _code, _title in EXIT_CODES.items():
        exit_codes[_title] = _code

    # for configuration
    app_name = 'tomcat-manager'
    app_author = 'tomcatmanager'
    config = None

    # new settings must to be defined at the class, not the instance
    timeout = 10
    status_prefix = '--'

    @property
    def status_to_stdout(self) -> bool:
        """Proxy property for feedback_to_output."""
        return self.feedback_to_output

    @status_to_stdout.setter
    def status_to_stdout(self, value: bool):
        """Proxy property for feedback_to_output."""
        self.feedback_to_output = value


    def __init__(self):
        # settings for cmd2.Cmd
        self.allow_cli_args = False

        self.abbrev = False
        self.echo = False
        unused = ['abbrev', 'continuation_prompt', 'feedback_to_output']
        for setting in unused:
            try:
                self.settable.pop(setting)
            except KeyError:
                pass
        self.settable.update({'echo': 'For piped input, echo command to output'})
        self.settable.update({'status_to_stdout': 'Status information to stdout instead of stderr'})
        self.settable.update({'editor': 'Program used to edit files'})
        self.settable.update({'timeout': 'Seconds to wait for HTTP connections'})
        self.settable.update({'status_prefix': 'String to prepend to all status output'})
        self.settable.update({'debug': 'Show stack trace for exceptions'})
        self.prompt = '{}> '.format(self.app_name)
        self.shortcuts.update({'$?': 'exit_code'})

        self.appdirs = appdirs.AppDirs(self.app_name, self.app_author)

        super().__init__(persistent_history_file=self.history_file)

        self.load_config()

        self.tomcat = tm.TomcatManager()
        self.tomcat.timeout = self.timeout
        self.exit_code = None

    ###
    #
    # Override cmd2.Cmd methods.
    #
    ###
    def poutput(self, msg: Any, end='\n'):
        """
        Convenient shortcut for self.stdout.write();
        by default adds newline to end if not already present.

        Also handles BrokenPipeError exceptions for when a commands's output
        has been piped to another process and that process terminates before
        the cmd2 command is finished executing.

        :param msg: str - message to print to current stdout - anyting
                          convertible to a str with '{}'.format() is OK
        :param end: str - string appended after the end of the message if
                          not already present, default a newline
        """
        if msg is not None:
            try:
                msg_str = '{}'.format(msg)
                self.stdout.write(msg_str)
                if not msg_str.endswith(end):
                    self.stdout.write(end)
            except BrokenPipeError:
                # This occurs if a command's output is being piped to another
                # process and that process closes before the command is
                # finished.
                pass

    def perror(self, errmsg: str, exception_type=None, traceback_war=True):
        """
        Print an error message or an exception.

        :param: errmsg          The error message to print. If None, then
                                print information about the exception
                                currently beging handled.
        :param: exception_type  From superclass. Ignored here.
        :param: traceback_war   From superclass. Ignored here.

        If debug=True, you will get a full stack trace, otherwise just the
        exception.
        """
        if errmsg:
            sys.stderr.write('{}\n'.format(errmsg))
        else:
            _type, _exception, _traceback = sys.exc_info()
            if _exception:
                if self.debug:
                    output = ''.join(traceback.format_exception(_type, _exception, _traceback))
                else:
                    output = ''.join(traceback.format_exception_only(_type, _exception))
                sys.stderr.write(output)

    def pfeedback(self, msg: str):
        """
        Print nonessential feedback.

        Set quiet=True to supress all feedback. If feedback_to_output=True,
        then feedback will be included in the output stream. Otherwise, it
        will be sent to sys.stderr.
        """
        if not self.quiet:
            fmt = '{}{}\n'
            if self.feedback_to_output:
                self.poutput(fmt.format(self.status_prefix, msg))
            else:
                sys.stderr.write(fmt.format(self.status_prefix, msg))

    def emptyline(self):
        """Do nothing on an empty line"""
        pass

    def default(self, statement: cmd2.Statement):
        """what to do if we don't recognize the command the user entered"""
        self.exit_code = self.exit_codes.command_not_found
        self.perror('unknown command: {}'.format(statement.command))

    ###
    #
    # Convenience and shared methods.
    #
    ###
    def docmd(self, func: Callable, *args, **kwargs) -> Any:
        """Call a function and return, printing any exceptions that occur

        Sets exit_code to 0 and calls {func}. If func throws a TomcatError,
        set exit_code to 1 and print the exception
        """
        self.exit_code = self.exit_codes.success
        r = func(*args, **kwargs)
        try:
            r.raise_for_status()
        except tm.TomcatError as err:
            self.exit_code = self.exit_codes.error
            self.perror(str(err))
        return r

    def show_help_from(self, argparser: argparse.ArgumentParser):
        """Set exit code and output help from an argparser."""
        self.exit_code = self.exit_codes.success
        self.poutput(argparser.format_help())

    def parse_args(self, parser: argparse.ArgumentParser, argv: List) -> argparse.Namespace:
        """Use argparse to parse a list of arguments a-la sys.argv"""
        # assume we get a usage error
        self.exit_code = self.exit_codes.usage
        # argv includes the command name, the arg parser doesn't
        # expect it, so let's omit it
        args = parser.parse_args(argv[1:])
        # no usage error, assume success
        self.exit_code = self.exit_codes.success
        return args

    def _which_server(self):
        """
        What url are we connected to and who are we connected as.

        Returns None if '.url` is None.
        """
        out = None
        if self.tomcat.url:
            out = 'connected to {}'.format(self.tomcat.url)
            if self.tomcat.user:
                out += ' as {}'.format(self.tomcat.user)
        return out

    @cmd2.with_argument_list
    def do_help(self, arglist: List):
        """Show available commands, or help on a specific command."""
        if arglist:
            # they want help on a specific command, use cmd2 for that
            super().do_help(arglist)
        else:
            # show a custom list of commands, organized by category
            help_ = []
            help_.append('tomcat-manager is a command line tool for managing a Tomcat server')

            help_ = self._help_add_header(help_, 'Connecting to a Tomcat server')
            help_.append('connect   {}'.format(self.do_connect.__doc__))
            help_.append('which     {}'.format(self.do_which.__doc__))

            help_ = self._help_add_header(help_, 'Managing applications')
            help_.append('list      {}'.format(self.do_list.__doc__))
            help_.append('deploy    {}'.format(self.do_deploy.__doc__))
            help_.append('redeploy  {}'.format(self.do_redeploy.__doc__))
            help_.append('undeploy  {}'.format(self.do_undeploy.__doc__))
            help_.append('start     {}'.format(self.do_start.__doc__))
            help_.append('stop      {}'.format(self.do_stop.__doc__))
            help_.append('restart   {}'.format(self.do_restart.__doc__))
            help_.append('  reload  Synonym for \'restart\'.')
            help_.append('sessions  {}'.format(self.do_sessions.__doc__))
            help_.append('expire    {}'.format(self.do_expire.__doc__))

            help_ = self._help_add_header(help_, 'Server information')
            help_.append('findleakers          {}'.format(self.do_findleakers.__doc__))
            help_.append('resources            {}'.format(self.do_resources.__doc__))
            help_.append('serverinfo           {}'.format(self.do_serverinfo.__doc__))
            help_.append('sslconnectorciphers  {}'.format(self.do_sslconnectorciphers.__doc__))
            help_.append('status               {}'.format(self.do_status.__doc__))
            help_.append('threaddump           {}'.format(self.do_threaddump.__doc__))
            help_.append('vminfo               {}'.format(self.do_vminfo.__doc__))

            help_ = self._help_add_header(help_, 'Settings, configuration, and tools')
            help_.append('config       {}'.format(self.do_config.__doc__))
            help_.append('edit         Edit a file in the preferred text editor.')
            help_.append('exit_code    {}'.format(self.do_exit_code.__doc__))
            help_.append('history      View, run, edit, and save previously entered commands.')
            help_.append('py           Execute python commands.')
            help_.append('pyscript     Run a file containing a python script.')
            help_.append('set          {}'.format(self.do_set.__doc__))
            help_.append('show         {}'.format(self.do_show.__doc__))
            help_.append('  settings   Synonym for \'show\'.')
            help_.append('shell        Execute a command in the operating system shell.')
            help_.append('shortcuts    Show shortcuts for other commands.')

            help_ = self._help_add_header(help_, 'Other')
            help_.append('exit     Exit this program.')
            help_.append('  quit   Synonym for \'exit\'.')
            help_.append('help     {}'.format(self.do_help.__doc__))
            help_.append('version  {}'.format(self.do_version.__doc__))
            help_.append('license  {}'.format(self.do_license.__doc__))

            for line in help_:
                self.poutput(line)
            self.exit_code = self.exit_codes.success

    @staticmethod
    def _help_add_header(help_: List, header: str) -> List:
        help_.append('')
        help_.append(header)
        help_.append('=' * 60)
        return help_

    ###
    #
    # user accessable commands for configuration and settings
    #
    ###
    config_parser = argparse.ArgumentParser(
        prog='config',
        description='Edit or show the location of the user configuration file.',
    )
    config_parser.add_argument(
        'action',
        choices=['edit', 'file'],
        help="""'file' shows the name of the configuration
             file. 'edit' edits the configuration file
             in your preferred editor."""
    )

    def do_config(self, cmdline: cmd2.Statement):
        """Edit or show the location of the user configuration file."""
        args = self.parse_args(self.config_parser, cmdline.argv)

        if args.action == 'file':
            self.poutput(self.config_file)
            self.exit_code = self.exit_codes.success
        else:
            if not self.editor:
                self.perror("no editor: use 'set editor={path}' to specify one")
                self.exit_code = self.exit_codes.error
                return

            # ensure the configuration directory exists
            configdir = os.path.dirname(self.config_file)
            if not os.path.exists(configdir):
                os.makedirs(configdir)

            # go edit the file
            cmd = '"{}" "{}"'.format(self.editor, self.config_file)
            self.pfeedback("executing {}".format(cmd))
            os.system(cmd)

            # read it back in and apply it
            self.pfeedback("reloading configuration")
            self.load_config()
            self.exit_code = self.exit_codes.success

    def help_config(self):
        """Show help for the 'config' command."""
        self.show_help_from(self.config_parser)

    show_parser = argparse.ArgumentParser(
        prog='show',
        description='Show all settings or a specific setting.',
    )
    show_parser.add_argument(
        'setting',
        nargs='?',
        help="""Name of the setting to show the value for.
             If omitted show the values of all settings."""
    )
    def do_show(self, cmdline: cmd2.Statement):
        """Show all settings or a specific setting."""
        args = self.parse_args(self.show_parser, cmdline.argv)

        result = {}
        maxlen = 0
        for setting in self.settable:
            if (not args.setting) or (setting == args.setting):
                val = str(getattr(self, setting))
                result[setting] = '{}={}'.format(setting, self._pythonize(val))
                maxlen = max(maxlen, len(result[setting]))
        # make a little extra space
        maxlen += 1
        if result:
            for setting in sorted(result):
                self.poutput('{}  # {}'.format(result[setting].ljust(maxlen),
                                               self.settable[setting]))
            self.exit_code = self.exit_codes.success
        else:
            self.perror("unknown setting: '{}'".format(args.setting))
            self.exit_code = self.exit_codes.error

    def help_show(self):
        """Show help for the 'show' command."""
        self.show_help_from(self.show_parser)

    settings_parser = argparse.ArgumentParser(
        prog='settings',
        description='Show all settings or a specific setting. Synonym for \'show\'.',
    )
    settings_parser.add_argument(
        'setting',
        nargs='?',
        help="""Name of the setting to show the value for.
             If omitted show the values of all settings."""
    )

    def do_settings(self, cmdline: cmd2.Statement):
        """Synonym for 'show' command."""
        self.do_show(cmdline)

    def help_settings(self):
        """Show help for the 'settings' command."""
        self.show_help_from(self.settings_parser)

    def do_set(self, args: cmd2.Statement):
        """Change program settings."""
        if args:
            config = EvaluatingConfigParser()
            setting_string = "[settings]\n{}".format(args)
            try:
                config.read_string(setting_string)
            except configparser.ParsingError:
                self.perror('invalid syntax: try {setting}={value}')
                self.exit_code = self.exit_codes.error
                return
            for param_name in config['settings']:
                if param_name in self.settable:
                    try:
                        self._change_setting(param_name, config['settings'][param_name])
                        self.exit_code = self.exit_codes.success
                    except ValueError as err:
                        if self.debug:
                            self.perror(None)
                        else:
                            self.perror(err)
                        self.exit_code = self.exit_codes.error
                else:
                    self.perror("unknown setting: '{}'".format(param_name))
                    self.exit_code = self.exit_codes.error
        else:
            self.perror('invalid syntax: try {setting}={value}')
            self.exit_code = self.exit_codes.usage

    def help_set(self):
        """Show help for the 'set' command."""
        self.exit_code = self.exit_codes.success
        self.poutput("""usage: set {setting}={value}

change the value of one of this program's settings

  setting  Name of the setting to modify. Use the 'show' command to see a
           list of valid settings.
  value    the value for the setting
""")

    ###
    #
    # other methods and properties related to configuration and settings
    #
    ###
    @property
    def config_file(self) -> str:
        """
        The location of the user configuration file.

        :return: The full path to the user configuration file, or None
                 if self.appdirs has not been defined.
        """
        if self.appdirs:
            filename = self.app_name + '.ini'
            return os.path.join(self.appdirs.user_config_dir, filename)
        return None

    @property
    def history_file(self) -> str:
        """
        The location of the command history file.

        :return: The full path to the file where command history will be
                saved and loaded, or None if self.appdirs has not been
                defined.
        """
        if self.appdirs:
            return os.path.join(self.appdirs.user_config_dir, 'history.txt')
        return None

    def load_config(self):
        """Open and parse the user config file and set self.config."""
        config = None
        if self.config_file is not None:
            config = EvaluatingConfigParser()
            try:
                with open(self.config_file, 'r') as fobj:
                    config.read_file(fobj)
            except FileNotFoundError:
                pass
        try:
            settings = config['settings']
            for key in settings:
                self._change_setting(key, settings[key])
        except KeyError:
            pass
        except ValueError:
            pass
        self.config = config

    def _change_setting(self, param_name: str, val: Any):
        """
        Apply a change to a setting, calling a hook if it is defined.

        This method is intended to only be called when the user requests the setting
        to be changed, either interactively or by loading the configuration file.

        param_name must be in settable or this method with throw a ValueError
        some parameters only accept boolean values, if you pass something that can't
        be converted to a boolean, throw a ValueError

        Call _onchange_{param_name}(old, new) after the setting changes value.
        """
        if param_name in self.settable:
            current_val = getattr(self, param_name)
            type_ = type(current_val)
            if type_ == bool:
                val = self.convert_to_boolean(val)
            elif type_ == int:
                try:
                    val = int(val)
                except ValueError:
                    # make a nicer error message
                    raise ValueError("invalid integer: '{}'".format(val))
            setattr(self, param_name, val)
            if current_val != val:
                try:
                    onchange_hook = getattr(self, '_onchange_{}'.format(param_name))
                    onchange_hook(current_val, val)
                except AttributeError:
                    pass
        else:
            raise ValueError

    def _onchange_timeout(self, _, new):
        """Pass the new timeout through to the TomcatManager object."""
        self.tomcat.timeout = new

    def convert_to_boolean(self, value: Any):
        """Return a boolean value translating from other types if necessary."""
        if isinstance(value, bool) is True:
            return value
        else:
            if str(value).lower() not in self.BOOLEAN_VALUES:
                if value is None or value == '':
                    raise ValueError('invalid syntax: must be true-ish or false-ish')
                else:
                    raise ValueError("invalid syntax: not a boolean: '{}'".format(value))
            return self.BOOLEAN_VALUES[value.lower()]

    @staticmethod
    def _pythonize(value: str):
        """Transform value into something the python interpreter can parse.

        Transform value into pvalue such that:

            value = ast.literal_eval(pvalue)

        This isn't quite true, because if there are no spaces or quote marks in value, then

            pvalue = value
        """
        single_quote = "'"
        double_quote = '"'
        pvalue = value
        if (single_quote in value) and (double_quote in value):
            # use sq as the outer quote, which means we have to
            # backslash all the other sq in the string
            value = value.replace(single_quote, '\\' + single_quote)
            pvalue = "'{}'".format(value)
        elif single_quote in value:
            pvalue = '"{}"'.format(value)
        elif double_quote in value:
            pvalue = "'{}'".format(value)
        elif ' ' in value:
            pvalue = "'{}'".format(value)
        return pvalue

    ###
    #
    # Connecting to Tomcat
    #
    ###
    connect_parser = argparse.ArgumentParser(
        prog='connect',
        description='connect to a tomcat manager instance',
        usage='%(prog)s [-h] config_name\n       %(prog)s [-h] url [user] [password]',
        epilog=""""If you specify a user and no password, you will be prompted for the
               password. If you don't specify a user or password, attempt to connect with
               no authentication.""",
    )
    connect_parser.add_argument(
        'config_name',
        nargs='?',
        help='a section from the config file which contains at least a url',
    )
    connect_parser.add_argument(
        'url',
        nargs='?',
        help='the url where the tomcat manager web app is located',
    )
    connect_parser.add_argument(
        'user',
        nargs='?',
        help='optional user to use for authentication',
    )
    connect_parser.add_argument(
        'password',
        nargs='?',
        help='optional password to use for authentication',
    )

    def do_connect(self, cmdline: cmd2.Statement):
        """Connect to a tomcat manager instance."""
        url = None
        user = None
        password = None
        args = self.parse_args(self.connect_parser, cmdline.argv)
        server = args.config_name
        if self.config.has_section(server):
            if self.config.has_option(server, 'url'):
                url = self.config[server]['url']
            if self.config.has_option(server, 'user'):
                user = self.config[server]['user']
            if self.config.has_option(server, 'password'):
                password = self.config[server]['password']
        else:
            # This is an ugly hack required to get argparse to show the help properly.
            # the argparser has both a config_name and a url positional argument.
            # If you only give config_name, and there isn't a section for it in
            # the configuration file, then it must be a url, so we have to
            # 'shift' the positional arguments to the left.
            url = args.config_name
            user = args.url
            password = args.user

        # prompt for password if necessary
        if url and user and not password:
            password = getpass.getpass()

        try:
            r = self.tomcat.connect(url, user, password)
            if r.ok:
                self.pfeedback(self._which_server())
                self.exit_code = self.exit_codes.success
            else:
                if self.debug:
                    # raise the exception and print the output
                    try:
                        r.raise_for_status()
                    except (requests.HTTPError, tm.TomcatError):
                        self.perror(None)
                        self.exit_code = self.exit_codes.error
                else:
                    # need to see whether we got an http error or whether
                    # tomcat wasn't at the url
                    if r.response.status_code == requests.codes.ok:
                        # there was some problem with the request, but we
                        # got http 200 OK. That means there was no tomcat
                        # at the url
                        self.perror('tomcat manager not found at {}'.format(url))
                    elif r.response.status_code == requests.codes.not_found:
                        # we connected, but the url was bad. No tomcat there
                        self.perror('tomcat manager not found at {}'.format(url))
                    else:
                        self.perror('http error: {} {}'.format(r.response.status_code,
                                                               responses[r.response.status_code]))
                    self.exit_code = self.exit_codes.error
        except requests.exceptions.ConnectionError:
            if self.debug:
                self.perror(None)
            else:
                self.perror('connection error')
            self.exit_code = self.exit_codes.error
        except requests.exceptions.Timeout:
            if self.debug:
                self.perror(None)
            else:
                self.perror('connection timeout')
            self.exit_code = self.exit_codes.error

    def help_connect(self):
        """Show help for the connect command."""
        self.show_help_from(self.connect_parser)


    which_parser = argparse.ArgumentParser(
        prog='which',
        description='show the url of the tomcat server you are connected to',
    )

    @requires_connection
    def do_which(self, cmdline: cmd2.Statement):
        """Show the url of the tomcat server you are connected to."""
        self.parse_args(self.which_parser, cmdline.argv)
        self.poutput(self._which_server())

    def help_which(self):
        """Show help for the 'which' command."""
        self.show_help_from(self.which_parser)


    ###
    #
    # commands for managing applications
    #
    ###
    def deploy_local(self, args: argparse.Namespace, update: bool = False):
        """Deploy a local war file to the tomcat server."""
        warfile = os.path.expanduser(args.warfile)
        with open(warfile, 'rb') as fileobj:
            self.exit_code = self.exit_codes.success
            self.docmd(self.tomcat.deploy_localwar, args.path, fileobj,
                       version=args.version, update=update)

    def deploy_server(self, args: argparse.Namespace, update: bool = False):
        """Deploy a war file to the tomcat server."""
        self.exit_code = self.exit_codes.success
        self.docmd(self.tomcat.deploy_serverwar, args.path, args.warfile,
                   version=args.version, update=update)

    def deploy_context(self, args: argparse.Namespace, update: bool = False):
        """Deploy a context xml file to the tomcat server."""
        self.exit_code = self.exit_codes.success
        self.docmd(self.tomcat.deploy_servercontext, args.path, args.contextfile,
                   warfile=args.warfile, version=args.version, update=update)

    deploy_parser = _deploy_parser(
        'deploy',
        'deploy an application to the tomcat server',
        deploy_local,
        deploy_server,
        deploy_context,
        )

    @requires_connection
    def do_deploy(self, cmdline: cmd2.Statement):
        """Deploy an application to the tomcat server."""
        args = self.parse_args(self.deploy_parser, cmdline.argv)
        try:
            args.func(self, args, update=False)
        except AttributeError:
            self.help_deploy()
            self.exit_code = self.exit_codes.error

    def help_deploy(self):
        """Show help for the deploy command."""
        self.show_help_from(self.deploy_parser)

    redeploy_parser = _deploy_parser(
        'redeploy',
        'deploy an application to the tomcat server, undeploying any application at the given path',
        deploy_local,
        deploy_server,
        deploy_context,
        )

    @requires_connection
    def do_redeploy(self, cmdline: cmd2.Statement):
        """Redeploy an application to the tomcat server."""
        args = self.parse_args(self.redeploy_parser, cmdline.argv)
        try:
            args.func(self, args, update=True)
        except AttributeError:
            self.help_redeploy()
            self.exit_code = self.exit_codes.error

    def help_redeploy(self):
        """Show help for the redeploy command."""
        self.show_help_from(self.redeploy_parser)


    undeploy_parser = _path_version_parser(
        'undeploy',
        'Remove an application at a given path from the tomcat server.'
    )

    @requires_connection
    def do_undeploy(self, cmdline: cmd2.Statement):
        """Remove an application from the tomcat server."""
        args = self.parse_args(self.undeploy_parser, cmdline.argv)
        self.docmd(self.tomcat.undeploy, args.path, args.version)

    def help_undeploy(self):
        """Help for the 'undeploy' command."""
        self.show_help_from(self.undeploy_parser)


    start_parser = _path_version_parser(
        'start',
        "Start a tomcat application that has been deployed but isn't running."
    )

    @requires_connection
    def do_start(self, cmdline: cmd2.Statement):
        """Start a deployed tomcat application that isn't running."""
        args = self.parse_args(self.start_parser, cmdline.argv)
        self.docmd(self.tomcat.start, args.path, args.version)

    def help_start(self):
        """Help for the 'start' command."""
        self.show_help_from(self.start_parser)


    stop_parser = _path_version_parser(
        'stop',
        'Stop a running tomcat application and leave it deployed on the server.'
    )

    @requires_connection
    def do_stop(self, cmdline: cmd2.Statement):
        """Stop a tomcat application and leave it deployed on the server."""
        args = self.parse_args(self.stop_parser, cmdline.argv)
        self.docmd(self.tomcat.stop, args.path, args.version)

    def help_stop(self):
        """Help for the 'stop' command."""
        self.show_help_from(self.stop_parser)


    reload_parser = _path_version_parser(
        'reload',
        'Start and stop a tomcat application. Synonym for \'restart\'.',
    )

    @requires_connection
    def do_reload(self, cmdline: cmd2.Statement):
        """Start and stop a tomcat application."""
        args = self.parse_args(self.reload_parser, cmdline.argv)
        self.docmd(self.tomcat.reload, args.path, args.version)

    def help_reload(self):
        """Help for the 'reload' command."""
        self.show_help_from(self.reload_parser)


    restart_parser = _path_version_parser(
        'restart',
        'Start and stop a tomcat application.',
    )

    @requires_connection
    def do_restart(self, cmdline: cmd2.Statement):
        """Start and stop a tomcat application."""
        args = self.parse_args(self.reload_parser, cmdline.argv)
        self.docmd(self.tomcat.reload, args.path, args.version)

    def help_restart(self):
        """Show help for the 'restart' command."""
        self.show_help_from(self.restart_parser)


    sessions_parser = argparse.ArgumentParser(
        prog='sessions',
        description='Show active sessions for a tomcat application.',
    )
    sessions_parser.add_argument(
        'path',
        help='The path part of the URL where the application is deployed.',
    )
    sessions_parser.add_argument(
        '-v', '--version',
        help="""Optional version string of the application from which to show sessions.
             If the application was deployed with a version string, it must be specified
             in order to show sessions.""",
    )

    @requires_connection
    def do_sessions(self, cmdline: cmd2.Statement):
        """Show active sessions for a tomcat application."""
        args = self.parse_args(self.sessions_parser, cmdline.argv)
        r = self.docmd(self.tomcat.sessions, args.path, args.version)
        if r.ok:
            self.poutput(r.sessions)

    def help_sessions(self):
        """Help for the 'sessions' command."""
        self.show_help_from(self.sessions_parser)


    expire_parser = argparse.ArgumentParser(
        prog='expire',
        description='expire idle sessions',
    )
    expire_parser.add_argument(
        '-v', '--version',
        help="""Optional version string of the application from which to expire sessions.
             If the application was deployed with a version string, it must be specified
             in order to expire sessions.""",
    )
    expire_parser.add_argument(
        'path',
        help='The path part of the URL where the application is deployed.',
    )
    expire_parser.add_argument(
        'idle',
        help="""Expire sessions idle for more than this number of minutes. Use
             0 to expire all sessions.""",
    )

    @requires_connection
    def do_expire(self, cmdline: cmd2.Statement):
        """Expire idle sessions."""
        args = self.parse_args(self.expire_parser, cmdline.argv)
        r = self.docmd(self.tomcat.expire, args.path, args.version, args.idle)
        if r.ok:
            self.poutput(r.sessions)

    def help_expire(self):
        """Help for the 'expire' command."""
        self.show_help_from(self.expire_parser)


    list_parser = argparse.ArgumentParser(
        prog='list',
        description='Show all installed applications',
        add_help=False,
    )
    list_parser.add_argument(
        '-r', '--raw',
        action='store_true',
        help='show apps without formatting',
    )
    list_parser.add_argument(
        '-s', '--state',
        choices=['running', 'stopped'],
        help='only show apps in a given state',
    )
    list_parser.add_argument(
        '-b', '--by',
        choices=['state', 'path'],
        default='state',
        help='sort by state (default), or sort by path',
    )

    @requires_connection
    def do_list(self, cmdline: cmd2.Statement):
        """Show all installed applications."""
        args = self.parse_args(self.list_parser, cmdline.argv)

        response = self.docmd(self.tomcat.list)
        if not response.ok:
            return

        apps = self._list_process_apps(response.apps, args)
        self.exit_code = self.exit_codes.success
        if args.raw:
            for app in apps:
                self.poutput(app)
        else:
            fmt = '{:24.24} {:7.7} {:>8.8} {:36.36}'
            dashes = '-'*80
            self.poutput(fmt.format('Path', 'State', 'Sessions', 'Directory'))
            self.poutput(fmt.format(dashes, dashes, dashes, dashes))
            for app in apps:
                self.poutput(
                    fmt.format(app.path, app.state, str(app.sessions), app.directory_and_version)
                )

    def help_list(self):
        """Show help for the 'list' command."""
        self.show_help_from(self.list_parser)

    @staticmethod
    def _list_process_apps(apps: List, args: argparse.Namespace):
        """
        Select and sort a list of `TomcatApplication` objects based on arguments

        We rely on the `TomcatApplication` object to determine the sort order.

        :return: a list of `TomcatApplication` objects
        """
        rtn = []
        # select the apps that should be included
        if args.state:
            rtn = filter(lambda app: app.state == args.state, apps)
        else:
            rtn = apps
        # now sort them
        if args.by == 'path':
            rtn = sorted(rtn, key=tm.models.TomcatApplication.sort_by_path_by_version_by_state)
        else:
            rtn = sorted(rtn, key=tm.models.TomcatApplication.sort_by_state_by_path_by_version)
        return rtn

    ###
    #
    # These commands that don't affect change, they just return some
    # information from the server.
    #
    ###
    serverinfo_parser = argparse.ArgumentParser(
        prog='serverinfo',
        description='show information about the tomcat server',
    )
    @requires_connection
    def do_serverinfo(self, cmdline: cmd2.Statement):
        """Show information about the tomcat server."""
        self.parse_args(self.serverinfo_parser, cmdline.argv)
        r = self.docmd(self.tomcat.server_info)
        self.poutput(r.result)

    def help_serverinfo(self):
        """Show help for the 'serverinfo' command."""
        self.show_help_from(self.serverinfo_parser)


    status_parser = argparse.ArgumentParser(
        prog='status',
        description='show server status information in xml format',
    )
    @requires_connection
    def do_status(self, cmdline: cmd2.Statement):
        """Show server status information in xml format."""
        self.parse_args(self.status_parser, cmdline.argv)
        r = self.docmd(self.tomcat.status_xml)
        root = xml.dom.minidom.parseString(r.status_xml)
        self.poutput(root.toprettyxml(indent='   '))

    def help_status(self):
        """Show help for the 'status' command."""
        self.show_help_from(self.status_parser)


    vminfo_parser = argparse.ArgumentParser(
        prog='vminfo',
        description='show diagnostic information about the jvm',
    )
    @requires_connection
    def do_vminfo(self, cmdline: cmd2.Statement):
        """Show diagnostic information about the jvm."""
        self.parse_args(self.vminfo_parser, cmdline.argv)
        r = self.docmd(self.tomcat.vm_info)
        self.poutput(r.vm_info)

    def help_vminfo(self):
        """Show help for the 'vminfo' command."""
        self.show_help_from(self.vminfo_parser)


    sslconnectorciphers_parser = argparse.ArgumentParser(
        prog='sslconnectorciphers',
        description='show SSL/TLS ciphers configured for each connector',
    )
    @requires_connection
    def do_sslconnectorciphers(self, cmdline: cmd2.Statement):
        """Show SSL/TLS ciphers configured for each connector."""
        self.parse_args(self.sslconnectorciphers_parser, cmdline.argv)
        r = self.docmd(self.tomcat.ssl_connector_ciphers)
        self.poutput(r.ssl_connector_ciphers)

    def help_sslconnectorciphers(self):
        """Show help for the 'sslconnectorciphers' command."""
        self.show_help_from(self.sslconnectorciphers_parser)


    threaddump_parser = argparse.ArgumentParser(
        prog='threaddump',
        description='show a jvm thread dump',
    )
    @requires_connection
    def do_threaddump(self, cmdline: cmd2.Statement):
        """Show a jvm thread dump."""
        self.parse_args(self.threaddump_parser, cmdline.argv)
        r = self.docmd(self.tomcat.thread_dump)
        self.poutput(r.thread_dump)

    def help_threaddump(self):
        """Show help for the 'threaddump' command."""
        self.show_help_from(self.threaddump_parser)


    resources_parser = argparse.ArgumentParser(
        prog='resources',
        description='show global JNDI resources configured in tomcat',
    )
    resources_parser.add_argument(
        'class_name',
        nargs='?',
        help='Optional fully qualified java class name of the resource type to show.',
    )
    @requires_connection
    def do_resources(self, cmdline: cmd2.Statement):
        """Show global JNDI resources configured in Tomcat."""
        args = self.parse_args(self.resources_parser, cmdline.argv)
        r = self.docmd(self.tomcat.resources, args.class_name)
        if r.resources:
            for resource, classname in iter(sorted(r.resources.items())):
                self.poutput('{}: {}'.format(resource, classname))
        else:
            self.exit_code = self.exit_codes.error

    def help_resources(self):
        """Show help for the 'resources' command."""
        self.show_help_from(self.resources_parser)


    findleakers_parser = argparse.ArgumentParser(
        prog='findleakers',
        description='show tomcat applications that leak memory',
        epilog="""WARNING: this triggers a full garbage collection on the server.
               Use with extreme caution on production systems."""
    )
    @requires_connection
    def do_findleakers(self, cmdline: cmd2.Statement):
        """Show tomcat applications that leak memory."""
        self.parse_args(self.findleakers_parser, cmdline.argv)
        r = self.docmd(self.tomcat.find_leakers)
        for leaker in r.leakers:
            self.poutput(leaker)

    def help_findleakers(self):
        """Show help for the 'findleakers' command."""
        self.show_help_from(self.findleakers_parser)

    ###
    #
    # miscellaneous user accessible commands
    #
    ###
    def do_exit(self, _):
        """Exit the interactive command prompt."""
        self.exit_code = self.exit_codes.success
        return self._STOP_AND_EXIT

    def do_quit(self, cmdline: cmd2.Statement):
        """Synonym for the 'exit' command."""
        return self.do_exit(cmdline)

    def do_eof(self, cmdline: cmd2.Statement):
        """Exit on the end-of-file character."""
        return self.do_exit(cmdline)

    version_parser = argparse.ArgumentParser(
        prog='version',
        description='show the version number of this program',
    )
    def do_version(self, cmdline: cmd2.Statement):
        """Show the version number of this program."""
        self.parse_args(self.version_parser, cmdline.argv)
        self.poutput(tm.VERSION_STRING)

    def help_version(self):
        """Show help for the 'version' command."""
        self.show_help_from(self.version_parser)


    exit_code_epilog = []
    exit_code_epilog.append('The codes have the following meanings:')
    for number, name in EXIT_CODES.items():
        exit_code_epilog.append('    {:3}  {}'.format(number, name.replace('_', ' ')))

    exit_code_parser = argparse.ArgumentParser(
        prog='exit_code',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='show a number indicating the status of the previous command',
        epilog='\n'.join(exit_code_epilog)
    )

    def do_exit_code(self, _):
        """Show a number indicating the status of the previous command."""
        # we don't use exit_code_parser here because we don't want to generate
        # spurrious exit codes, i.e. if they have incorrect usage on the
        # exit_code command

        # don't set the exit code here, just show it
        self.poutput(self.exit_code)

    def help_exit_code(self):
        """Show help for the 'exit_code' command."""
        self.show_help_from(self.exit_code_parser)


    license_parser = argparse.ArgumentParser(
        prog='license',
        description='show the software license for this program',
    )

    def do_license(self, cmdline: cmd2.Statement):
        """Show the software license for this program."""
        self.parse_args(self.license_parser, cmdline.argv)
        self.poutput("""
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
        """Show help for the 'license' command."""
        self.show_help_from(self.license_parser)


# pylint: disable=too-many-ancestors
class EvaluatingConfigParser(configparser.ConfigParser):
    """Subclass of configparser.ConfigParser which evaluates values on get()."""
    # pylint: disable=arguments-differ
    def get(self, section, option, **kwargs):
        val = super().get(section, option, **kwargs)
        if "'" in val or '"' in val:
            try:
                val = ast.literal_eval(val)
            except ValueError:
                pass
        return val
