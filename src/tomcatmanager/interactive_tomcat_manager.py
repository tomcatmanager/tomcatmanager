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
# pylint: disable=too-many-lines

import argparse
import ast
import configparser
import getpass
import http.client
import os
import pathlib
import sys
import textwrap
import traceback
import xml.dom.minidom
from typing import Callable, Any, List

import appdirs
import cmd2
import requests
import rich
import rich.console
import tomlkit

import tomcatmanager as tm


def requires_connection(func: Callable) -> Callable:
    """Decorator for interactive methods which require a connection."""

    def _requires_connection(self, *args, **kwargs):
        if self.tomcat and self.tomcat.is_connected:
            func(self, *args, **kwargs)
        else:
            # print the message
            self.exit_code = self.EXIT_ERROR
            self.perror("not connected")

    _requires_connection.__doc__ = func.__doc__
    return _requires_connection


def _path_version_parser(cmdname: str, helpmsg: str) -> argparse.ArgumentParser:
    """Construct an argparser using the given parameters"""
    parser = argparse.ArgumentParser(prog=cmdname, description=helpmsg)
    parser.add_argument(
        "-v",
        "--version",
        help=(
            f"Optional version string of the application to"
            f" {cmdname}. If the application was deployed with"
            f" a version string, it must be specified in order to"
            f" {cmdname} the application."
        ),
    )
    path_help = "The path part of the URL where the application is deployed."
    parser.add_argument("path", help=path_help)
    return parser


def _deploy_parser(
    name: str,
    desc: str,
    localfunc: Callable,
    serverfunc: Callable,
    contextfunc: Callable,
) -> argparse.ArgumentParser:
    """Construct a argument parser for the deploy or redeploy commands."""
    deploy_parser = argparse.ArgumentParser(
        prog=name,
        description=desc,
    )
    deploy_subparsers = deploy_parser.add_subparsers(title="methods", dest="method")
    # local subparser
    deploy_local_parser = deploy_subparsers.add_parser(
        "local",
        description="transmit a locally available warfile to the server",
        help="transmit a locally available warfile to the server",
    )
    deploy_local_parser.add_argument(
        "-v", "--version", help="version string to associate with this deployment"
    )
    deploy_local_parser.add_argument("warfile")
    deploy_local_parser.add_argument("path")
    deploy_local_parser.set_defaults(func=localfunc)
    # server subparser
    deploy_server_parser = deploy_subparsers.add_parser(
        "server",
        description="deploy a warfile already on the server",
        help="deploy a warfile already on the server",
    )
    deploy_server_parser.add_argument(
        "-v", "--version", help="version string to associate with this deployment"
    )
    deploy_server_parser.add_argument("warfile")
    deploy_server_parser.add_argument("path")
    deploy_server_parser.set_defaults(func=serverfunc)
    # context subparser
    deploy_context_parser = deploy_subparsers.add_parser(
        "context",
        description="deploy a contextfile already on the server",
        help="deploy a contextfile already on the server",
    )
    deploy_context_parser.add_argument(
        "-v",
        "--version",
        help="version string to associate with this deployment",
    )
    deploy_context_parser.add_argument("contextfile")
    deploy_context_parser.add_argument("warfile", nargs="?")
    deploy_context_parser.add_argument("path")
    deploy_context_parser.set_defaults(func=contextfunc)
    return deploy_parser


# pylint: disable=too-many-public-methods, too-many-instance-attributes
class InteractiveTomcatManager(cmd2.Cmd):
    """An interactive command line tool for the Tomcat Manager web application.

    each command sets the value of the instance variable exit_code,
    which mirrors bash standard values for exit codes (available via $?)
    """

    # exit codes for exit_code attribute
    EXIT_SUCCESS = 0
    EXIT_ERROR = 1
    EXIT_USAGE = 2
    EXIT_COMMAND_NOT_FOUND = 127
    # for the help displaying the exit code meanings
    EXIT_CODES = {
        # 'number': 'name'
        EXIT_SUCCESS: "success",
        EXIT_ERROR: "error",
        EXIT_USAGE: "usage",
        EXIT_COMMAND_NOT_FOUND: "command not found",
    }

    # Possible boolean values
    BOOLEAN_VALUES = {
        "1": True,
        "yes": True,
        "y": True,
        "true": True,
        "t": True,
        "on": True,
        "0": False,
        "no": False,
        "n": False,
        "false": False,
        "f": False,
        "off": False,
    }

    # for configuration
    app_name = "tomcat-manager"
    app_author = "tomcatmanager"
    config = tomlkit.loads("")

    @property
    def status_to_stdout(self) -> bool:
        """Proxy property for feedback_to_output."""
        return self.feedback_to_output

    @status_to_stdout.setter
    def status_to_stdout(self, value: bool):
        """Proxy property for feedback_to_output."""
        self.feedback_to_output = value

    @property
    def timeout(self) -> float:
        """Proxy property for timeout"""
        return self.tomcat.timeout

    @timeout.setter
    def timeout(self, value: float):
        """Proxy property for timeout"""
        self.tomcat.timeout = value

    def __init__(self):
        self.appdirs = appdirs.AppDirs(self.app_name, self.app_author)
        shortcuts = {"?": "help", "!": "shell", "$?": "exit_code"}

        super().__init__(
            persistent_history_file=self.history_file,
            persistent_history_length=1000,
            shortcuts=shortcuts,
            allow_cli_args=False,
            terminators=[],
            auto_load_commands=False,
            include_py=True,
        )

        self.self_in_py = True

        to_remove = [
            "max_completion_items",
            "always_show_hint",
            "debug",
            "echo",
            "editor",
            "feedback_to_output",
            "prompt",
        ]
        for setting in to_remove:
            try:
                self.remove_settable(setting)
            except KeyError:
                pass

        self.add_settable(
            cmd2.Settable(
                "echo",
                self.convert_to_boolean,
                "For piped input, echo command to output",
                self,
            )
        )
        self.add_settable(
            cmd2.Settable(
                "status_to_stdout",
                self.convert_to_boolean,
                "Status information to stdout instead of stderr",
                self,
            )
        )
        self.add_settable(
            cmd2.Settable(
                "status_prefix", str, "String to prepend to all status output", self
            )
        )
        self.add_settable(
            cmd2.Settable("editor", str, "Program used to edit files", self)
        )
        self.add_settable(
            cmd2.Settable(
                "timeout", float, "Seconds to wait for HTTP connections", self
            )
        )
        self.add_settable(
            cmd2.Settable(
                "prompt", str, "The prompt displayed before accepting user input", self
            )
        )
        self.add_settable(
            cmd2.Settable(
                "debug",
                self.convert_to_boolean,
                "Show stack trace for exceptions",
                self,
            )
        )

        self.tomcat = tm.TomcatManager()

        # set default values
        self.prompt = f"{self.app_name}> "
        self.debug = False
        self.timeout = 10
        self.status_prefix = "--"
        self.echo = False

        # set up the rich theme and console
        tomcat_theme = rich.theme.Theme(
            {
                "tm.help.section": "gold1",
                "tm.help.command": "magenta3",
                "tm.feedback": "deep_sky_blue1",
                "tm.error": "red3",
                "tm.status": "deep_sky_blue1",
                "tm.list.header": "bold deep_sky_blue1",
                "tm.list.border": "bold deep_sky_blue1",
                "tm.app.running": "green1",
                "tm.app.stopped": "red3",
                "tm.app.sessions": "cyan1",
            }
        )
        self.console = rich.console.Console(
            theme=tomcat_theme, markup=False, emoji=False, highlight=False
        )
        self.error_console = rich.console.Console(
            stderr=True, theme=tomcat_theme, markup=False, emoji=False, highlight=False
        )

        # load config file if it exists
        self.load_config()
        # give a friendly message if there is an old config file but not a
        # new one
        if (
            not self.config_file.exists() and self.config_file_old.exists()
        ):  # pragma: nocover
            self.pfeedback(
                "In version 6.0.0 the configuration file format changed from INI to TOML."
            )
            self.pfeedback(
                "You have a configuration file in the old format. Type 'config convert' to"
            )
            self.pfeedback("migrate your old configuration to the new format.")

        # initialize command exit code
        self.exit_code = None

    ###
    #
    # Override cmd2.Cmd methods.
    #
    ###
    def poutput(self, msg: Any = "", *, end: str = "\n") -> None:
        """
        Convenient shortcut for self.stdout.write();
        by default adds newline to end if not already present.

        Also handles BrokenPipeError exceptions for when a commands's output
        has been piped to another process and that process terminates before
        the cmd2 command is finished executing.

        :param msg: str - message to print to current stdout - anyting
                          convertible to a str with f"{msg}" is OK
        :param end: str - string appended after the end of the message if
                          not already present, default a newline
        """
        if msg is not None:
            try:
                msg_str = f"{msg}"
                ##self.stdout.write(msg_str)
                self.console.print(msg_str, end=end)
                # if not msg_str.endswith(end):
                #     ##self.stdout.write(end)
                #     self.console.print(end)
            except BrokenPipeError:  # pragma: nocover
                # This occurs if a command's output is being piped to another
                # process and that process closes before the command is
                # finished.
                pass

    # pylint: disable=unused-argument
    def perror(self, msg: Any = "", *, end: str = "\n", apply_style=False) -> None:
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
        if msg:
            ##sys.stderr.write(f"{msg}{end}")
            self.error_console.print(f"{msg}", end=end, style="tm.error")
        else:
            _type, _exception, _traceback = sys.exc_info()
            if _exception:
                # if self.debug:
                #    output = ''.join(traceback.format_exception(_type, _exception, _traceback))
                # else:
                #    output = ''.join(traceback.format_exception_only(_type, _exception))
                output = "".join(traceback.format_exception_only(_type, _exception))
                ##sys.stderr.write(output)
                self.error_console.print(output, end=end)

    def pfeedback(self, msg: Any, *, end: str = "\n") -> None:
        """
        Print nonessential feedback.

        Set quiet=True to suppress all feedback. If feedback_to_output=True,
        then feedback will be included in the output stream. Otherwise, it
        will be sent to sys.stderr.
        """
        if not self.quiet:
            formatted_msg = f"{self.status_prefix}{msg}"
            if self.feedback_to_output:
                ##self.poutput(formatted_msg)
                self.console.print(formatted_msg, end=end, style="tm.feedback")
            else:
                ## sys.stderr.write(formatted_msg)
                self.error_console.print(formatted_msg, end=end, style="tm.feedback")

    def emptyline(self):
        """Do nothing on an empty line"""

    def default(self, statement: cmd2.Statement):
        """what to do if we don't recognize the command the user entered"""
        self.exit_code = self.EXIT_COMMAND_NOT_FOUND
        self.perror(f"unknown command: {statement.command}")

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
        self.exit_code = self.EXIT_ERROR
        try:
            r = func(*args, **kwargs)
            r.raise_for_status()
            self.exit_code = self.EXIT_SUCCESS
            return r
        except tm.TomcatNotImplementedError:
            self.perror("command not implemented by server")
            return None
        except tm.TomcatError as err:
            self.perror(str(err))
            return None

    def show_help_from(self, argparser: argparse.ArgumentParser):
        """Set exit code and output help from an argparser."""
        self.exit_code = self.EXIT_SUCCESS
        self.poutput(argparser.format_help())

    def parse_args(
        self, parser: argparse.ArgumentParser, argv: List
    ) -> argparse.Namespace:
        """Use argparse to parse a list of arguments a-la sys.argv"""
        # assume we get a usage error
        self.exit_code = self.EXIT_USAGE
        # argv includes the command name, the arg parser doesn't
        # expect it, so let's omit it
        try:
            args = parser.parse_args(argv[1:])
        except SystemExit as sysexit:
            # argparse throws SystemExit if an argument parse error occurs
            # cmd2 will exit to the shell if this exception is raised
            # we have to catch it
            raise cmd2.Cmd2ArgparseError from sysexit

        # no usage error, assume success
        self.exit_code = self.EXIT_SUCCESS
        return args

    def _which_server(self):
        """
        What url are we connected to and who are we connected as.

        Returns None if not connected to a server.
        """
        out = None
        if self.tomcat.is_connected:
            out = f"connected to {self.tomcat.url}"
            if self.tomcat.user:
                out += f" as {self.tomcat.user}"
            if self.tomcat.cert:
                if isinstance(self.tomcat.cert, tuple):
                    # get the key
                    _, authby = self.tomcat.cert
                else:
                    authby = self.tomcat.cert
                out += f" authenticated by {authby}"

        return out

    def _help_section(self, title: str):
        """Start a new help section and return a table for commands in that section"""
        self.console.print("")
        self.console.print(title, style="tm.help.section")
        self.console.print("─" * 72, style="tm.help.section")
        cmds = rich.table.Table(
            show_edge=False,
            box=None,
            padding=(0, 3, 0, 0),
            show_header=False,
        )
        return cmds

    def _help_command(self, table, command, desc):
        """Add a new command to a help table"""
        table.add_row(rich.text.Text(command, style="tm.help.command"), desc)

    def do_help(self, args: str):
        """Show available commands, or help on a specific command."""
        # pylint: disable=too-many-statements
        if args:
            # they want help on a specific command, use cmd2 for that
            super().do_help(args)
        else:
            self.console.print("tomcat-manager", style="tm.help.command", end="")
            self.console.print(" is a command line tool for managing a Tomcat server")
            self.console.print()
            self.console.print("Type 'help [command]' for help on any command.")
            self.console.print()
            self.console.print("Here's a categorized list of all available commands:")

            cmds = self._help_section("Connecting to a Tomcat server")
            self._help_command(cmds, "connect", self.do_connect.__doc__)
            self._help_command(cmds, "which", self.do_which.__doc__)
            self.console.print(cmds)

            cmds = self._help_section("Managing applications")
            self._help_command(cmds, "list", self.do_list.__doc__)
            self._help_command(cmds, "deploy", self.do_deploy.__doc__)
            self._help_command(cmds, "redeploy", self.do_redeploy.__doc__)
            self._help_command(cmds, "undeploy", self.do_undeploy.__doc__)
            self._help_command(cmds, "start", self.do_start.__doc__)
            self._help_command(cmds, "stop", self.do_stop.__doc__)
            self._help_command(cmds, "restart", self.do_restart.__doc__)
            self._help_command(cmds, "  reload", "Synonym for 'restart'")
            self._help_command(cmds, "sessions", self.do_sessions.__doc__)
            self._help_command(cmds, "expire", self.do_expire.__doc__)
            self.console.print(cmds)

            cmds = self._help_section("Server information")
            self._help_command(cmds, "findleakers", self.do_findleakers.__doc__)
            self._help_command(cmds, "resources", self.do_resources.__doc__)
            self._help_command(cmds, "serverinfo", self.do_serverinfo.__doc__)
            self._help_command(cmds, "status", self.do_status.__doc__)
            self._help_command(cmds, "threaddump", self.do_threaddump.__doc__)
            self._help_command(cmds, "vminfo", self.do_vminfo.__doc__)
            self.console.print(cmds)

            cmds = self._help_section("TLS configuration")
            self._help_command(
                cmds, "sslconnectorciphers", self.do_sslconnectorciphers.__doc__
            )
            self._help_command(
                cmds, "sslconnectorcerts", self.do_sslconnectorcerts.__doc__
            )
            self._help_command(
                cmds,
                "sslconnectortrustedcerts",
                self.do_sslconnectortrustedcerts.__doc__,
            )
            self._help_command(cmds, "sslreload", self.do_sslreload.__doc__)
            self.console.print(cmds)

            cmds = self._help_section("Settings, configuration, and tools")
            self._help_command(cmds, "config", self.do_config.__doc__)
            self._help_command(
                cmds, "edit", "Edit a file in the preferred text editor."
            )
            self._help_command(cmds, "exit_code", self.do_exit_code.__doc__)
            self._help_command(
                cmds,
                "history",
                "View, run, edit, and save previously entered commands.",
            )
            self._help_command(cmds, "py", "Run an interactive python shell.")
            self._help_command(
                cmds, "run_pyscript", "Run a file containing a python script."
            )
            self._help_command(cmds, "set", self.do_set.__doc__)
            self._help_command(cmds, "show", self.do_show.__doc__)
            self._help_command(cmds, "  settings", "Synonym for 'show'.")
            self._help_command(
                cmds, "shell", "Execute a command in the operating system shell."
            )
            self._help_command(cmds, "shortcuts", "Show shortcuts for other commands.")
            self.console.print(cmds)

            cmds = self._help_section("Other")
            self._help_command(cmds, "exit", "Exit this program.")
            self._help_command(cmds, "  quit", "Synonym for 'exit'.")
            self._help_command(cmds, "help", self.do_help.__doc__)
            self._help_command(cmds, "version", self.do_version.__doc__)
            self._help_command(cmds, "license", self.do_license.__doc__)
            self.console.print(cmds)

            self.exit_code = self.EXIT_SUCCESS

    @staticmethod
    def _help_add_header(help_: List, header: str) -> List:
        help_.append("")
        help_.append(header)
        help_.append("=" * 60)
        return help_

    ###
    #
    # user accessable commands for configuration and settings
    #
    ###
    config_parser = argparse.ArgumentParser(
        prog="config",
        description="Edit or show the location of the user configuration file.",
    )
    config_parser.add_argument(
        "action",
        choices=["edit", "file", "convert"],
        help="""'file' shows the name of the configuration
             file. 'edit' edits the configuration file
             in your preferred editor. 'convert' writes a new .toml
             configuration file with the same settings as the old
             .ini configuration file.""",
    )

    def do_config(self, cmdline: cmd2.Statement):
        """Edit or show the location of the user configuration file."""
        args = self.parse_args(self.config_parser, cmdline.argv)

        if args.action == "file":
            self.poutput(self.config_file)
            self.exit_code = self.EXIT_SUCCESS
        elif args.action == "edit":
            self._config_edit()
        elif args.action == "convert":
            self._config_convert()

    def help_config(self):
        """Show help for the 'config' command."""
        self.show_help_from(self.config_parser)

    def _config_edit(self):
        """
        Open the configuration file in an editor, and reload the configuration when the
        editor exits.
        """
        if not self.editor:
            self.perror("no editor: use 'set editor={path}' to specify one")
            self.exit_code = self.EXIT_ERROR
            return

        # ensure the configuration directory exists
        configdir = self.config_file.parent
        if not configdir.exists():  # pragma: nocover
            configdir.mkdir(parents=True, exist_ok=True)

        # go edit the file
        cmd = f'"{self.editor}" "{self.config_file}"'
        self.pfeedback(f"executing {cmd}")
        os.system(cmd)

        # read it back in and apply it
        self.pfeedback("reloading configuration")
        self.load_config()
        self.exit_code = self.EXIT_SUCCESS

    def _config_convert(self):
        """
        Convert the old .ini based configuration file into the new .toml
        based one.

        The .ini file _must_ exist and the .toml file _must not_ exist in order
        for this to do anything.
        """
        if self.config_file.exists():
            self.pfeedback(
                "configuration file exists: cowardly refusing to overwrite it"
            )
            self.exit_code = self.EXIT_ERROR
            return

        if not self.config_file_old.exists():
            self.pfeedback("old configuration file does not exist: nothing to convert")
            self.exit_code = self.EXIT_ERROR
            return

        self.pfeedback("converting old configuration file to new format")
        iniconfig = EvaluatingConfigParser()
        with open(self.config_file_old, "r", encoding="utf-8") as fobj:
            iniconfig.read_file(fobj)
            # convert it to a new toml file
            toml = tomlkit.document()
            for section in dict(iniconfig).keys():
                if section == "DEFAULT":
                    pass
                elif section == "settings":
                    table = tomlkit.table()
                    for param_name in dict(iniconfig[section]):
                        # inifiles are untyped so everything is read from
                        # them as a string. this code converts the string
                        # to the proper type, so that it gets written into
                        # the toml file as the proper type
                        try:
                            settable = self.settables[param_name]
                            value = iniconfig[section][param_name]
                            value = cmd2.utils.strip_quotes(value)
                            table.add(param_name, settable.val_type(value))
                        except KeyError:
                            # we found a setting in the file that isn't a valid
                            # setting for this program, bail out
                            self.pfeedback(
                                f"conversion failed: '{param_name}' is not a valid setting"
                            )
                            self.exit_code = self.EXIT_ERROR
                            return
                    toml.add(section, table)
                else:
                    # all the other sections/tables are servers
                    table = tomlkit.table()
                    for key in dict(iniconfig[section]):
                        value = iniconfig[section][key]
                        # all values here are strings, except for 'verify' which
                        # is a boolen. Let's check for that and convert if necessary
                        if key == "verify":
                            value = self.convert_to_boolean(value)
                        table.add(key, value)
                    toml.add(section, table)

            with open(self.config_file, "w", encoding="utf-8") as ftoml:
                ftoml.write(tomlkit.dumps(toml))
                self.pfeedback(f"configuration written to {self.config_file}")

        # read it back in and apply it
        self.pfeedback("reloading configuration")
        self.load_config()
        self.exit_code = self.EXIT_SUCCESS

    show_parser = argparse.ArgumentParser(
        prog="show",
        description="Show all settings or a specific setting.",
    )
    show_parser.add_argument(
        "setting",
        nargs="?",
        help="""Name of the setting to show the value for.
             If omitted show the values of all settings.""",
    )

    def do_show(self, cmdline: cmd2.Statement):
        """Show all settings or a specific setting."""
        args = self.parse_args(self.show_parser, cmdline.argv)

        result = {}
        maxlen = 0
        for setting in self.settables:
            if (not args.setting) or (setting == args.setting):
                val = str(getattr(self, setting))
                result[setting] = f"{setting}={self._pythonize(val)}"
                maxlen = max(maxlen, len(result[setting]))
        # make a little extra space
        maxlen += 1
        if result:
            for setting in sorted(result):
                self.poutput(
                    (
                        f"{result[setting].ljust(maxlen)}"
                        f"  # {self.settables[setting].description}"
                    )
                )
            self.exit_code = self.EXIT_SUCCESS
        else:
            self.perror(f"unknown setting: '{args.setting}'")
            self.exit_code = self.EXIT_ERROR

    def help_show(self):
        """Show help for the 'show' command."""
        self.show_help_from(self.show_parser)

    settings_parser = argparse.ArgumentParser(
        prog="settings",
        description="Show all settings or a specific setting. Synonym for 'show'.",
    )
    settings_parser.add_argument(
        "setting",
        nargs="?",
        help="""Name of the setting to show the value for.
             If omitted show the values of all settings.""",
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
            setting_string = f"[settings]\n{args}"
            try:
                config.read_string(setting_string)
            except configparser.ParsingError:
                self.perror("invalid syntax: try 'set {setting} = {value}'")
                self.exit_code = self.EXIT_ERROR
                return
            for param_name in config["settings"]:
                if param_name in self.settables:
                    try:
                        self._change_setting(param_name, config["settings"][param_name])
                        self.exit_code = self.EXIT_SUCCESS
                    except ValueError as err:
                        if self.debug:
                            self.perror(None)
                        else:
                            self.perror(err)
                        self.exit_code = self.EXIT_ERROR
                else:
                    self.perror(f"unknown setting: '{param_name}'")
                    self.exit_code = self.EXIT_ERROR
        else:
            self.do_show(args)

    def help_set(self):
        """Show help for the 'set' command."""
        self.exit_code = self.EXIT_SUCCESS
        self.poutput(
            """usage: set {setting}={value}

change the value of one of this program's settings

  setting  Name of the setting to modify. Use the 'show' command to see a
           list of valid settings.
  value    the value for the setting
"""
        )

    ###
    #
    # other methods and properties related to configuration and settings
    #
    ###
    @property
    def config_file(self) -> pathlib.Path:
        """
        The location of the user configuration file.

        :return: The full path to the user configuration file, or None
                 if self.appdirs has not been defined.
        """
        if self.appdirs:
            filename = self.app_name + ".toml"
            return pathlib.Path(self.appdirs.user_config_dir).resolve() / filename
        return None

    @property
    def config_file_old(self) -> pathlib.Path:
        """
        The location of the old configuration file, using the .ini extension and
        format.

        As of 6.0.0 this file is no longer used, instead we use a .toml file available
        in `config_file`. This property exists so we can convert the old file to the
        new format

        :return: The full path to the old user configuration file, or None
                 if self.appdirs has not been defined.
        """
        if self.appdirs:
            filename = self.app_name + ".ini"
            return pathlib.Path(self.appdirs.user_config_dir).resolve() / filename
        return None

    @property
    def history_file(self) -> pathlib.Path:
        """
        The location of the command history file.

        :return: The full path to the file where command history will be
                saved and loaded, or None if self.appdirs has not been
                defined.
        """
        if self.appdirs:
            return pathlib.Path(self.appdirs.user_config_dir).resolve() / "history.txt"
        return None

    def load_config(self):
        """Open and parse the user config file and set self.config."""
        config = tomlkit.loads("")
        if self.config_file is not None:
            try:
                with open(self.config_file, "r", encoding="utf-8") as fobj:
                    config = tomlkit.loads(fobj.read())
            except FileNotFoundError:
                pass
        try:
            settings = config["settings"]
            for key in settings:
                self._change_setting(key, settings[key])
        except KeyError:
            pass
        except ValueError:
            pass
        self.config = config

    def _change_setting(self, param_name: str, value: Any):
        """
        Apply a change to a setting, calling a hook if it is defined.

        This method is intended to only be called when the user requests the setting
        to be changed, either interactively or by loading the configuration file.

        param_name must be in settable or this method with throw a ValueError
        some parameters only accept boolean values, if you pass something that can't
        be converted to a boolean, throw a ValueError

        Calls the settable onchange callback if it exists.
        """
        try:
            settable = self.settables[param_name]
            # calling set_value should fire any on change callbacks
            settable.set_value(value)
        except KeyError as keyerr:
            raise ValueError(f"invalid setting: {param_name}") from keyerr

    @classmethod
    def convert_to_boolean(cls, value: Any):
        """Return a boolean value translating from other types if necessary."""
        if isinstance(value, bool) is True:
            return value

        if str(value).lower() not in cls.BOOLEAN_VALUES:
            if value is None or value == "":
                raise ValueError("invalid syntax: must be true-ish or false-ish")
            # we can't figure out what it is
            raise ValueError(f"invalid syntax: not a boolean: '{value}'")
        return cls.BOOLEAN_VALUES[value.lower()]

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
            value = value.replace(single_quote, "\\" + single_quote)
            pvalue = f"'{value}'"
        elif single_quote in value:
            pvalue = f'"{value}"'
        elif double_quote in value:
            pvalue = f"'{value}'"
        elif " " in value:
            pvalue = f"'{value}'"
        return pvalue

    ###
    #
    # Connecting to Tomcat
    #
    ###
    connect_parser = argparse.ArgumentParser(
        prog="connect",
        description="connect to a tomcat manager instance",
        usage="%(prog)s [-h] config_name\n       %(prog)s [-h] url [user] [password]",
        epilog="""If you specify a user and no password, you will be prompted for the
               password.""",
    )
    connect_parser.add_argument(
        "config_name",
        nargs="?",
        help="a section from the config file which contains at least a url",
    )
    connect_parser.add_argument(
        "url",
        nargs="?",
        help="the url where the tomcat manager web app is located",
    )
    connect_parser.add_argument(
        "user",
        nargs="?",
        help="optional user to use for authentication",
    )
    connect_parser.add_argument(
        "password",
        nargs="?",
        help="optional password to use for authentication",
    )
    connect_parser.add_argument(
        "--cert",
        action="store",
        help="""path to certificate for client side authentication;
        file can include private key, in which case --key is unnecessary""",
    )
    connect_parser.add_argument(
        "--key",
        action="store",
        help="path to private key for client side authentication",
    )
    connect_parser.add_argument(
        "--cacert",
        action="store",
        help="""path to certificate authority bundle or directory used to
        validate server SSL/TLS certificate""",
    )
    connect_parser.add_argument(
        "--noverify",
        # store_true makes the default False, aka default is to verify
        # server certificates
        action="store_true",
        help="don't validate server SSL certificates, overrides --cacert",
    )

    def do_connect(self, cmdline: cmd2.Statement):
        """Connect to a tomcat manager instance."""
        # pylint: disable=too-many-branches, too-many-statements
        # define some variables that we will either fill from a server shortcut
        # or from arguments
        url = None
        user = None
        password = None
        cert = None
        key = None
        cacert = None
        verify = True

        args = self.parse_args(self.connect_parser, cmdline.argv)
        server = args.config_name
        if server in self.config.keys():
            if "url" in self.config[server].keys():
                url = self.config[server]["url"]
            if "user" in self.config[server].keys():
                user = self.config[server]["user"]
            if "password" in self.config[server].keys():
                password = self.config[server]["password"]
            if "cert" in self.config[server].keys():
                cert = self.config[server]["cert"]
            if "key" in self.config[server].keys():
                key = self.config[server]["key"]
            if "cacert" in self.config[server].keys():
                cacert = self.config[server]["cacert"]
            if "verify" in self.config[server].keys():
                verify = self.config[server]["verify"]
        else:
            # This is an ugly hack required to get argparse to show the help properly.
            # the argparser has both a config_name and a url positional argument.
            # If you only give config_name, and there isn't a section for it in
            # the configuration file, then it must be a url, so we have to
            # 'shift' the positional arguments to the left.
            url = args.config_name

        if args.url:
            user = args.url
            # can't set the password if you don't set the user because
            # these arguments are positional
            if args.user:
                password = args.user
        # end of ugly hack

        # prompt for password if necessary
        if url and user and not password:
            password = getpass.getpass()

        # allow command line arguments to override server options
        # that's why this code isn't in the big if statement above

        # set ssl client validation
        if args.cert:
            cert = args.cert
        if args.key:
            key = args.key
        if cert and key:
            cert = (cert, key)

        # set ssl server certificate validation
        if args.noverify:
            # if you say not to verify SSL certs, this overrides --cacert
            verify = False
        if args.cacert:
            cacert = args.cacert

        if verify and cacert:
            # when verify is false, cacert doesn't matter
            # when it's true, then we can override with cacert
            verify = cacert

        with self.console.status("[bold blue]connecting", spinner="dots"):
            try:
                r = self.tomcat.connect(url, user, password, verify=verify, cert=cert)

                if r.ok:
                    self.pfeedback(self._which_server())
                    if r.server_info.tomcat_version:
                        self.pfeedback(
                            f"tomcat version: {r.server_info.tomcat_version}"
                        )
                    self.exit_code = self.EXIT_SUCCESS
                else:
                    if self.debug:
                        # raise the exception and print the output
                        try:
                            r.raise_for_status()
                        except (requests.HTTPError, tm.TomcatError):
                            self.perror(None)
                            self.exit_code = self.EXIT_ERROR
                    else:
                        # need to see whether we got an http error or whether
                        # tomcat wasn't at the url
                        if r.response.status_code == requests.codes.ok:
                            # there was some problem with the request, but we
                            # got http 200 OK. That means there was no tomcat
                            # at the url
                            self.perror(f"tomcat manager not found at {url}")
                        elif r.response.status_code == requests.codes.not_found:
                            # we connected, but the url was bad. No tomcat there
                            self.perror(f"tomcat manager not found at {url}")
                        else:
                            self.perror(
                                (
                                    f"http error: {r.response.status_code}"
                                    f" {http.client.responses[r.response.status_code]}"
                                )
                            )
                        self.exit_code = self.EXIT_ERROR
            except requests.exceptions.ConnectionError:
                if self.debug:
                    self.perror(None)
                else:
                    self.perror("connection error")
                self.exit_code = self.EXIT_ERROR
            except requests.exceptions.Timeout:
                if self.debug:
                    self.perror(None)
                else:
                    self.perror("connection timeout")
                self.exit_code = self.EXIT_ERROR

    def help_connect(self):
        """Show help for the connect command."""
        self.show_help_from(self.connect_parser)

    which_parser = argparse.ArgumentParser(
        prog="which",
        description="show the url of the tomcat server you are connected to",
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
        warfile = pathlib.Path(args.warfile).expanduser()
        with open(warfile, "rb") as fileobj:
            self.exit_code = self.EXIT_SUCCESS
            self.docmd(
                self.tomcat.deploy_localwar,
                args.path,
                fileobj,
                version=args.version,
                update=update,
            )

    def deploy_server(self, args: argparse.Namespace, update: bool = False):
        """Deploy a war file to the tomcat server."""
        self.exit_code = self.EXIT_SUCCESS
        self.docmd(
            self.tomcat.deploy_serverwar,
            args.path,
            args.warfile,
            version=args.version,
            update=update,
        )

    def deploy_context(self, args: argparse.Namespace, update: bool = False):
        """Deploy a context xml file to the tomcat server."""
        self.exit_code = self.EXIT_SUCCESS
        self.docmd(
            self.tomcat.deploy_servercontext,
            args.path,
            args.contextfile,
            warfile=args.warfile,
            version=args.version,
            update=update,
        )

    deploy_parser = _deploy_parser(
        "deploy",
        "deploy an application to the tomcat server",
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
        except AttributeError:  # pragma: nocover
            self.help_deploy()
            self.exit_code = self.EXIT_ERROR

    def help_deploy(self):
        """Show help for the deploy command."""
        self.show_help_from(self.deploy_parser)

    redeploy_parser = _deploy_parser(
        "redeploy",
        "deploy an application to the tomcat server, undeploying any application at the given path",
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
        except AttributeError:  # pragma: nocover
            self.help_redeploy()
            self.exit_code = self.EXIT_ERROR

    def help_redeploy(self):
        """Show help for the redeploy command."""
        self.show_help_from(self.redeploy_parser)

    undeploy_parser = _path_version_parser(
        "undeploy", "Remove an application at a given path from the tomcat server."
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
        "start", "Start a tomcat application that has been deployed but isn't running."
    )

    @requires_connection
    def do_start(self, cmdline: cmd2.Statement):
        """Start a deployed tomcat application that isn't running."""
        args = self.parse_args(self.start_parser, cmdline.argv)
        taskname = args.path
        if args.version:
            taskname += f"##{args.version}"
        status = rich.text.Text(f"starting {taskname}", style="tm.status")
        with self.console.status(status, spinner="dots"):
            r = self.docmd(self.tomcat.start, args.path, args.version)
            if r and self.exit_code == self.EXIT_SUCCESS:
                self.pfeedback(f"started {taskname}")

    def help_start(self):
        """Help for the 'start' command."""
        self.show_help_from(self.start_parser)

    stop_parser = _path_version_parser(
        "stop", "Stop a running tomcat application and leave it deployed on the server."
    )

    @requires_connection
    def do_stop(self, cmdline: cmd2.Statement):
        """Stop a tomcat application and leave it deployed on the server."""
        args = self.parse_args(self.stop_parser, cmdline.argv)
        taskname = args.path
        if args.version:
            taskname += f"##{args.version}"
        status = rich.text.Text(f"stopping {taskname}", style="tm.status")
        with self.console.status(status, spinner="dots"):
            r = self.docmd(self.tomcat.stop, args.path, args.version)
            if r and self.exit_code == self.EXIT_SUCCESS:
                self.pfeedback(f"stopped {taskname}")

    def help_stop(self):
        """Help for the 'stop' command."""
        self.show_help_from(self.stop_parser)

    reload_parser = _path_version_parser(
        "reload",
        "Stop and start a tomcat application. Synonym for 'restart'.",
    )

    @requires_connection
    def do_reload(self, cmdline: cmd2.Statement):
        """Stop and start a tomcat application."""
        args = self.parse_args(self.reload_parser, cmdline.argv)
        self.docmd(self.tomcat.reload, args.path, args.version)

    def help_reload(self):
        """Help for the 'reload' command."""
        self.show_help_from(self.reload_parser)

    restart_parser = _path_version_parser(
        "restart",
        "Stop and start a tomcat application.",
    )

    @requires_connection
    def do_restart(self, cmdline: cmd2.Statement):
        """Stop and start a tomcat application."""
        args = self.parse_args(self.reload_parser, cmdline.argv)
        self.docmd(self.tomcat.reload, args.path, args.version)

    def help_restart(self):
        """Show help for the 'restart' command."""
        self.show_help_from(self.restart_parser)

    sessions_parser = argparse.ArgumentParser(
        prog="sessions",
        description="Show active sessions for a tomcat application.",
    )
    sessions_parser.add_argument(
        "path",
        help="The path part of the URL where the application is deployed.",
    )
    sessions_parser.add_argument(
        "-v",
        "--version",
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
        prog="expire",
        description="expire idle sessions",
    )
    expire_parser.add_argument(
        "-v",
        "--version",
        help="""Optional version string of the application from which to expire sessions.
             If the application was deployed with a version string, it must be specified
             in order to expire sessions.""",
    )
    expire_parser.add_argument(
        "path",
        help="The path part of the URL where the application is deployed.",
    )
    expire_parser.add_argument(
        "idle",
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
        prog="list",
        description="Show all installed applications",
        add_help=False,
    )
    list_parser.add_argument(
        "-r",
        "--raw",
        action="store_true",
        help="show apps without formatting",
    )
    list_parser.add_argument(
        "-s",
        "--state",
        choices=["running", "stopped"],
        help="only show apps in a given state",
    )
    list_parser.add_argument(
        "-b",
        "--by",
        choices=["state", "path"],
        default="state",
        help="sort by state (default), or sort by path",
    )

    @requires_connection
    def do_list(self, cmdline: cmd2.Statement):
        """Show all installed applications."""
        args = self.parse_args(self.list_parser, cmdline.argv)

        response = self.docmd(self.tomcat.list)
        if response.ok:
            apps = self._list_process_apps(response.apps, args)
            self.exit_code = self.EXIT_SUCCESS
            if args.raw:
                for app in apps:
                    self.poutput(app)
            else:
                table = rich.table.Table(
                    box=rich.box.HORIZONTALS,
                    show_edge=False,
                    padding=(0, 2, 0, 0),
                    header_style="tm.list.header",
                    border_style="tm.list.border",
                )
                table.add_column("Path")
                table.add_column("State")
                table.add_column("Sessions", justify="right")
                table.add_column("Directory")
                for app in apps:
                    state_style = f"tm.app.{app.state.value}"
                    table.add_row(
                        app.path,
                        rich.text.Text(app.state.value, style=state_style),
                        rich.text.Text(str(app.sessions), style="tm.app.sessions"),
                        app.directory_and_version,
                    )
                self.console.print(table)

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
            filter_state = tm.models.ApplicationState.parse(args.state)
            rtn = filter(lambda app: app.state == filter_state, apps)
        else:
            rtn = apps
        # now sort them
        if args.by == "path":
            rtn = sorted(
                rtn, key=tm.models.TomcatApplication.sort_by_path_by_version_by_state
            )
        else:
            rtn = sorted(
                rtn, key=tm.models.TomcatApplication.sort_by_state_by_path_by_version
            )
        return rtn

    ###
    #
    # These commands that don't affect change, they just return some
    # information from the server.
    #
    ###
    serverinfo_parser = argparse.ArgumentParser(
        prog="serverinfo",
        description="show information about the tomcat server",
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
        prog="status",
        description="show server status information in xml format",
    )

    @requires_connection
    def do_status(self, cmdline: cmd2.Statement):
        """Show server status information in xml format."""
        self.parse_args(self.status_parser, cmdline.argv)
        r = self.docmd(self.tomcat.status_xml)
        root = xml.dom.minidom.parseString(r.status_xml)
        self.poutput(root.toprettyxml(indent="   "))

    def help_status(self):
        """Show help for the 'status' command."""
        self.show_help_from(self.status_parser)

    vminfo_parser = argparse.ArgumentParser(
        prog="vminfo",
        description="show diagnostic information about the jvm",
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
        prog="sslconnectorciphers",
        description="show SSL/TLS ciphers configured for each connector",
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

    sslconnectorcerts_parser = argparse.ArgumentParser(
        prog="sslconnectorcerts",
        description="show SSL/TLS certificate chain for each connector",
    )

    @requires_connection
    def do_sslconnectorcerts(self, cmdline: cmd2.Statement):
        """Show SSL/TLS certificate chain for each connector."""
        self.parse_args(self.sslconnectorcerts_parser, cmdline.argv)
        r = self.docmd(self.tomcat.ssl_connector_certs)
        self.poutput(r.ssl_connector_certs)

    def help_sslconnectorcerts(self):
        """Show help for the 'sslconnectorcerts' command."""
        self.show_help_from(self.sslconnectorcerts_parser)

    sslconnectortrustedcerts_parser = argparse.ArgumentParser(
        prog="sslconnectortrustedcerts",
        description="show SSL/TLS trusted certificates for each connector",
    )

    @requires_connection
    def do_sslconnectortrustedcerts(self, cmdline: cmd2.Statement):
        """Show SSL/TLS trusted certificates for each connector."""
        self.parse_args(self.sslconnectortrustedcerts_parser, cmdline.argv)
        r = self.docmd(self.tomcat.ssl_connector_trusted_certs)
        self.poutput(r.ssl_connector_trusted_certs)

    def help_sslconnectortrustedcerts(self):
        """Show help for the 'sslconnectortrustedcerts' command."""
        self.show_help_from(self.sslconnectortrustedcerts_parser)

    sslreload_parser = argparse.ArgumentParser(
        prog="sslreload",
        description="reload SSL/TLS certificates and keys",
    )
    sslreload_parser.add_argument(
        "host_name",
        nargs="?",
        help="Optional host name to reload SSL/TLS certificates and keys for.",
    )

    @requires_connection
    def do_sslreload(self, cmdline: cmd2.Statement):
        """Reload SSL/TLS certificates and keys."""
        args = self.parse_args(self.sslreload_parser, cmdline.argv)
        r = self.docmd(self.tomcat.ssl_reload, args.host_name)
        if r and r.ok:
            self.pfeedback(r.status_message)

    def help_sslreload(self):
        """Show help for the 'resources' command."""
        self.show_help_from(self.sslreload_parser)

    threaddump_parser = argparse.ArgumentParser(
        prog="threaddump",
        description="show a jvm thread dump",
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
        prog="resources",
        description="show global JNDI resources configured in tomcat",
    )
    resources_parser.add_argument(
        "class_name",
        nargs="?",
        help="Optional fully qualified java class name of the resource type to show.",
    )

    @requires_connection
    def do_resources(self, cmdline: cmd2.Statement):
        """Show global JNDI resources configured in Tomcat."""
        args = self.parse_args(self.resources_parser, cmdline.argv)
        r = self.docmd(self.tomcat.resources, args.class_name)
        if r.resources:
            for resource, classname in iter(sorted(r.resources.items())):
                self.poutput(f"{resource}: {classname}")
        else:
            self.exit_code = self.EXIT_ERROR

    def help_resources(self):
        """Show help for the 'resources' command."""
        self.show_help_from(self.resources_parser)

    findleakers_parser = argparse.ArgumentParser(
        prog="findleakers",
        description="show tomcat applications that leak memory",
        epilog="""WARNING: this triggers a full garbage collection on the server.
               Use with extreme caution on production systems.""",
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
        self.exit_code = self.EXIT_SUCCESS
        return True

    def do_quit(self, cmdline: cmd2.Statement):
        """Synonym for the 'exit' command."""
        return self.do_exit(cmdline)

    def do_eof(self, cmdline: cmd2.Statement):
        """Exit on the end-of-file character."""
        return self.do_exit(cmdline)

    version_parser = argparse.ArgumentParser(
        prog="version",
        description="show the version number of this program",
    )

    def do_version(self, cmdline: cmd2.Statement):
        """Show the version number of this program."""
        self.parse_args(self.version_parser, cmdline.argv)
        self.poutput(tm.VERSION_STRING)

    def help_version(self):
        """Show help for the 'version' command."""
        self.show_help_from(self.version_parser)

    exit_code_epilog = []
    exit_code_epilog.append("The codes have the following meanings:")
    for number, name in EXIT_CODES.items():
        exit_code_epilog.append(f"    {number:3}  {name}")

    exit_code_parser = argparse.ArgumentParser(
        prog="exit_code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="show a number indicating the status of the previous command",
        epilog="\n".join(exit_code_epilog),
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
        prog="license",
        description="show the software license for this program",
    )

    def do_license(self, cmdline: cmd2.Statement):
        """Show the software license for this program."""
        self.parse_args(self.license_parser, cmdline.argv)
        mitlicense = textwrap.dedent(
            """\
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
            """
        )
        self.poutput(mitlicense)

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
            except ValueError:  # pragma: nocover
                pass
        return val
