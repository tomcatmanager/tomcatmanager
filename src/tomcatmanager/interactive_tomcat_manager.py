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
import contextlib
import enum
import getpass
import http.client

import importlib.resources as importlib_resources

try:
    _ = importlib_resources.files
except AttributeError:  # pragma: nocover
    # python < 3.8 doesn't have .files in the standard library importlib.resources
    # we'll go get the one from pypi, which has it
    # pylint: disable=import-error
    import importlib_resources  # type: ignore

import os
import pathlib
import shutil
import sys
import textwrap
import traceback
import xml.dom.minidom
from typing import Callable, Any, List, Dict

import appdirs
import cmd2
import requests
import rich
import rich.console
import rich.spinner
import rich.syntax
import rich.progress
from rich_argparse import RichHelpFormatter, RawDescriptionRichHelpFormatter
import tomlkit

import tomcatmanager as tm


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

    # list of known scopes that themes can apply color to
    THEME_SCOPES = [
        "tm.error",
        "tm.status",
        "tm.animation",
        "tm.help.category",
        "tm.help.border",
        "tm.help.command",
        "tm.help.args",
        "tm.usage.prog",
        "tm.usage.groups",
        "tm.usage.args",
        "tm.usage.metavar",
        "tm.usage.help",
        "tm.usage.text",
        "tm.usage.syntax",
        "tm.list.header",
        "tm.list.border",
        "tm.app.running",
        "tm.app.stopped",
        "tm.app.sessions",
        "tm.setting.name",
        "tm.setting.equals",
        "tm.setting.comment",
        "tm.setting.string",
        "tm.setting.bool",
        "tm.setting.int",
        "tm.setting.float",
        "tm.theme.category",
        "tm.theme.border",
        "tm.theme.name",
    ]

    THEME_URL = "https://raw.githubusercontent.com/tomcatmanager/themes/main"

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

    @property
    def status_animation(self) -> str:
        """Validating property for activity animation type"""
        return self._status_animation

    @status_animation.setter
    def status_animation(self, value: str):
        """Validating property for activity animation type"""
        if value:
            try:
                _ = rich.spinner.Spinner(value)
            except KeyError as err:
                # the spinner doesn't exist, rich throws a KeyError for this,
                # we need a ValueError. KeyError puts the message in single quotes
                # err.args[0] gets the message without the quotes
                raise ValueError(err.args[0]) from err
            self._status_animation = value
        else:
            # use empty string instead of None because TOML doesn't nave None or Nil
            self._status_animation = ""

    @property
    def theme(self) -> str:
        """Validating property for theme specification"""
        return self._theme

    @theme.setter
    def theme(self, value: str):
        """Validating property for theme specification"""
        if self._apply_theme(value):
            self._theme = value

    def _set_defaults(self):
        """Set default values for all settings"""
        self.prompt = f"{self.app_name}> "
        self.debug = False
        self.timeout = 10.0
        self.status_prefix = "--"
        self.echo = False
        self.quiet = False
        self.status_suffix = "..."
        self.status_animation = "bouncingBar"
        self.theme = ""
        # go apply the empty theme, which sets
        # self.console and self.error_console
        self._apply_theme(self.theme)

    # pylint: disable=too-many-statements
    def __init__(self, loadconfig=True):
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
            "allow_style",
            "feedback_to_output",
            "quiet",
            "debug",
            "echo",
            "editor",
            "prompt",
        ]
        for setting in to_remove:
            try:
                self.remove_settable(setting)
            except KeyError:
                pass

        self.add_settable(
            cmd2.Settable(
                "quiet",
                _to_bool,
                "suppress all feedback and status output",
                self,
            )
        )
        self.add_settable(
            cmd2.Settable(
                "debug",
                _to_bool,
                "show stack trace for exceptions",
                self,
            )
        )
        self.add_settable(
            cmd2.Settable(
                "echo",
                _to_bool,
                "for piped input, echo command to output",
                self,
            )
        )
        self.add_settable(
            cmd2.Settable("editor", str, "program used to edit files", self)
        )
        self.add_settable(
            cmd2.Settable(
                "status_to_stdout",
                bool,
                "status information to stdout instead of stderr",
                self,
            )
        )
        self.add_settable(
            cmd2.Settable(
                "status_prefix", str, "string to prepend to all status output", self
            )
        )
        self.add_settable(
            cmd2.Settable("prompt", str, "displays before accepting user input", self)
        )
        self.add_settable(
            cmd2.Settable(
                "timing",
                _to_bool,
                "report execution time upon command completion",
                self,
            )
        )
        self.add_settable(
            cmd2.Settable(
                "timeout", float, "seconds to wait for HTTP connections", self
            )
        )
        self.add_settable(
            cmd2.Settable(
                "status_suffix", str, "suffix to append to status messages", self
            )
        )
        self.add_settable(
            cmd2.Settable(
                "status_animation",
                str,
                "style of activity animation from rich.spinner",
                self,
            )
        )
        self.add_settable(cmd2.Settable("theme", str, "color scheme", self))

        self.tomcat = tm.TomcatManager()

        # set default values
        self._set_defaults()

        # load config file if it exists
        if loadconfig:
            self.load_config()
        else:
            self.pfeedback("skipping load of configuration file")

        # give a friendly message if there is an old config file but not a
        # new one
        if self.config_file and not self.config_file.exists():  # pragma: nocover
            if (
                self.config_file_old and self.config_file_old.exists()
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
    # Theme and rendering helpers
    #
    ###
    def _apply_theme(self, theme: str) -> bool:
        """Apply a given theme

        :returns: True of the theme could be applied, False if not
        """
        # the scopes have to be present in the theme, or else it generates
        # errors. Create a theme with all the scopes set to 'none', which
        # tells rich.style to apply no styling
        tvalues = {}
        for scope in self.THEME_SCOPES:
            tvalues[scope] = "none"
        # if we have a theme name given
        if theme:
            # find the ThemeLocation and path, we discard the former
            # here, because we don't care
            _, tfile = self._resolve_theme(theme)
            if not tfile:
                self.perror(f"unknown theme: '{theme}'")
                return False

            try:
                with open(tfile, encoding="utf-8") as file_var:
                    newvalues = tomlkit.load(file_var)
            except (tomlkit.exceptions.TOMLKitError, OSError) as err:
                self.perror(f"error loading theme: {err}")
                return False

            # apply the new values from the theme to tvalues
            for scope in self.THEME_SCOPES:
                parts = scope.split(".")
                style = ""
                try:
                    if len(parts) == 2:
                        style = newvalues[parts[0]][parts[1]]
                    elif len(parts) == 3:
                        style = newvalues[parts[0]][parts[1]][parts[2]]
                except tomlkit.exceptions.NonExistentKey:
                    # the theme file doesn't define that scope
                    pass
                if style:
                    tvalues[scope] = style
        # copy the usage styles to the RichHelpFormatter class
        for style in ["prog", "groups", "args", "metavar", "help", "text", "syntax"]:
            RichHelpFormatter.styles[f"argparse.{style}"] = tvalues[f"tm.usage.{style}"]
        # set other RichHelpFormatter settings
        RichHelpFormatter.usage_markup = True
        # default is str.title, which shows the groups in title case
        # this shows the groups in all lower case
        RichHelpFormatter.group_name_formatter = str.lower

        # recreate our console objects using the new theme
        try:
            self.console = rich.console.Console(
                theme=rich.theme.Theme(tvalues),
                markup=False,
                emoji=False,
                highlight=False,
            )
            self.error_console = rich.console.Console(
                stderr=True,
                theme=rich.theme.Theme(tvalues),
                markup=False,
                emoji=False,
                highlight=False,
            )
        except (rich.errors.StyleError, rich.errors.ConsoleError) as err:
            self.perror(f"error loading theme: {err}")
            return False
        return True

    def _resolve_theme(self, name: str) -> pathlib.Path:
        """
        Find the path of the theme file for a given name.

        :return: a tuple of ThemeLocation, and the path of the theme file for
                 the given name, or None, None if no theme file for that
                 name exists

        Checks in the user theme directory first, which is located
        in user configuration directory in a "themes" directory.
        If not found, then it looks in the embedded themes included
        as part of tomcatmanager.
        """
        # check user theme dir
        tfile = self.user_theme_dir / f"{name}.toml"
        if tfile.is_file():
            return ThemeLocation.USER, tfile
        # check included themes
        for path in importlib_resources.files("tomcatmanager.themes").iterdir():
            if path.name == f"{name}.toml":
                return ThemeLocation.BUILTIN, path
        # couldn't find it
        return None, None

    def _progressfactory(self, message: str) -> rich.progress.Progress:
        """generate a progress object"""
        if self.quiet or not message:
            # return a no-op context manager (that means we won't get any output)
            return contextlib.nullcontext()

        if self.feedback_to_output:
            cons = self.console
        else:
            cons = self.error_console

        # create a custom status/progress display
        msg = rich.text.Text(
            f"{self.status_prefix}{message}{self.status_suffix}",
            style="tm.status",
        )
        text_column = rich.progress.RenderableColumn(msg)
        if self.status_animation:
            spinner_column = rich.progress.SpinnerColumn(
                spinner_name=self.status_animation,
                style="tm.animation",
            )
            progress = rich.progress.Progress(text_column, spinner_column, console=cons)
        else:
            progress = rich.progress.Progress(text_column, console=cons)
        # gotta have a task in order for the status spinner to render,
        # but the name we use here doesn't matter
        progress.add_task("notshown")
        return progress

    def _apptag(self, path: str, version: str) -> str:
        """Render an message with an app tag"""
        apptag = path
        if version:
            apptag += f"##{version}"
        return apptag

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
        try:
            self.console.print(msg, end=end)
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
                self.console.print(formatted_msg, end=end, style="tm.status")
            else:
                self.error_console.print(formatted_msg, end=end, style="tm.status")

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
    def docmd(self, statustxt: str, func: Callable, *args, **kwargs) -> Any:
        """Call a function and return, printing any exceptions that occur

        Sets exit_code to 0 and calls {func}. If func throws a TomcatError,
        set exit_code to 1 and print the exception
        """
        self.exit_code = self.EXIT_ERROR
        try:
            with self._progressfactory(statustxt):
                r = func(*args, **kwargs)
            r.raise_for_status()
            self.exit_code = self.EXIT_SUCCESS
            if r.status_message and r.status_message != tm.StatusCode.OK.value:
                # don't print the status message if it's just "OK"
                self.pfeedback(r.status_message)
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
        # we don't use self.console because this already has ansi color codes in
        self.ppaged(argparser.format_help())

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

    def raise_if_not_connected(self):
        """Print an error and throw an exception if we are not connected"""
        if self.tomcat and self.tomcat.is_connected:
            return
        # we aren't connected, so make a fuss
        self.exit_code = self.EXIT_ERROR
        self.perror("not connected")
        # this exception tells cmd2 to skip the post command hooks and
        # just prompt for more input
        raise cmd2.Cmd2ArgparseError

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
        self.console.print(title, style="tm.help.category")
        self.console.print("─" * 72, style="tm.help.border")
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

    # pylint: disable=too-many-statements
    def do_help(self, args: cmd2.Statement):
        """show available commands, or help on a specific command"""
        if args:
            # cmd2 doesn't handle help for subparsers very well
            # I want "help deploy local" to work. so....
            if args.arg_list[0] in ["deploy", "redeploy"]:
                self._do_help_deploy(args)
            elif args.arg_list[0] == "theme":
                self._do_help_theme(args)
            else:
                # use cmd2 for commands without subparsers
                super().do_help(args)
                if self.last_result:
                    self.exit_code = self.EXIT_SUCCESS
                else:
                    self.exit_code = self.EXIT_ERROR
        else:
            with self.console.pager(styles=True):
                self.console.print("tomcat-manager", style="tm.help.command", end="")
                self.console.print(
                    " is a command line tool for managing a Tomcat server"
                )
                self.console.print()
                helpcmd = rich.text.Text("Type '")
                helpcmd.append("help", style="tm.help.command")
                helpcmd.append(" ")
                helpcmd.append("[command]", style="tm.help.args")
                helpcmd.append("' for help on any command.")
                self.console.print(helpcmd)
                self.console.print()
                self.console.print(
                    "Here's a categorized list of all available commands:"
                )

                cmds = self._help_section("Connecting to a Tomcat server")
                self._help_command(cmds, "connect", self.do_connect.__doc__)
                self._help_command(cmds, "which", self.do_which.__doc__)
                self._help_command(cmds, "disconnect", self.do_disconnect.__doc__)
                self.console.print(cmds)

                cmds = self._help_section("Managing applications")
                self._help_command(cmds, "list", self.do_list.__doc__)
                self._help_command(cmds, "deploy", self.do_deploy.__doc__)
                self._help_command(cmds, "redeploy", self.do_redeploy.__doc__)
                self._help_command(cmds, "undeploy", self.do_undeploy.__doc__)
                self._help_command(cmds, "start", self.do_start.__doc__)
                self._help_command(cmds, "stop", self.do_stop.__doc__)
                self._help_command(cmds, "restart", self.do_restart.__doc__)
                self._help_command(cmds, "  reload", "synonym for 'restart'")
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
                self._help_command(cmds, "settings", self.do_settings.__doc__)
                self._help_command(cmds, "set", self.do_set.__doc__)
                self._help_command(cmds, "config", self.do_config.__doc__)
                self._help_command(cmds, "theme", self.do_theme.__doc__)
                self._help_command(
                    cmds, "edit", "edit a file in the preferred text editor"
                )
                self._help_command(cmds, "exit_code", self.do_exit_code.__doc__)
                self._help_command(
                    cmds,
                    "history",
                    "view, run, edit, and save previously entered commands",
                )
                self._help_command(cmds, "py", "run an interactive python shell")
                self._help_command(
                    cmds, "run_pyscript", "run a file containing a python script"
                )
                self._help_command(
                    cmds, "shell", "execute a command in the operating system shell"
                )
                self._help_command(
                    cmds, "shortcuts", "show shortcuts for other commands"
                )
                self.console.print(cmds)

                cmds = self._help_section("Other")
                self._help_command(cmds, "exit", self.do_exit.__doc__)
                self._help_command(cmds, "  quit", self.do_quit.__doc__)
                self._help_command(cmds, "help", self.do_help.__doc__)
                self._help_command(cmds, "version", self.do_version.__doc__)
                self._help_command(cmds, "license", self.do_license.__doc__)
                self.console.print(cmds)

            self.exit_code = self.EXIT_SUCCESS

    def _do_help_deploy(self, args: cmd2.Statement):
        """do help for the deploy and redeploy commands"""
        # if we get here we know args.arg_list[0] is deploy or redeploy
        command = args.arg_list[0]
        (parser, local_parser, server_parser, context_parser) = _deploy_parser(
            command,
            self.do_deploy.__doc__,
            self.deploy_local,
            self.deploy_server,
            self.deploy_context,
        )
        if len(args.arg_list) == 2:
            # help deploy local
            subcommand = args.arg_list[1]
            if subcommand in ["local", "server", "context"]:
                # format help from subparser
                (_, local_parser, server_parser, context_parser) = _deploy_parser(
                    "deploy",
                    self.do_deploy.__doc__,
                    self.deploy_local,
                    self.deploy_server,
                    self.deploy_context,
                )
                # this output is already formatted and knows about the length of
                # the non-printing ascii color sequences. don't write it to
                # our console or it will get wrapped inappropriately
                if subcommand == "local":
                    self.console.print(local_parser.format_help())
                elif subcommand == "server":
                    self.console.print(server_parser.format_help())
                elif subcommand == "context":
                    self.console.print(context_parser.format_help())
                self.exit_code = self.EXIT_SUCCESS
            else:
                # they typed 'help deploy invalidcommand'
                self.console.print(parser.format_help())
                self.exit_code = self.EXIT_SUCCESS
        else:
            # we have some wacko arguments, so just do help for deploy/redeploy
            self.console.print(parser.format_help())
            self.exit_code = self.EXIT_SUCCESS

    def _do_help_theme(self, args: cmd2.Statement):
        """do help for the theme command"""
        # if we get here we know args.arg_list[0] is 'theme'
        parsers = self._build_theme_parsers()
        if len(args.arg_list) == 2:
            subcommand = args.arg_list[1]
            if subcommand in parsers:
                self.console.print(parsers[subcommand].format_help())
                self.exit_code = self.EXIT_SUCCESS
            else:
                # they typed 'help theme invalidaction'
                self.console.print(parsers["theme"].format_help())
                self.exit_code = self.EXIT_SUCCESS
        else:
            # we have some wacko arguments, so just do help for the main command
            self.console.print(parsers["theme"].format_help())
            self.exit_code = self.EXIT_SUCCESS

    ###
    #
    # user accessable commands for configuration and settings
    #
    ###
    @property
    def config_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the config command."""
        parser = argparse.ArgumentParser(
            prog="config",
            description=self.do_config.__doc__,
            formatter_class=RichHelpFormatter,
        )
        parser.add_argument(
            "action",
            choices=["edit", "file", "convert"],
            help="""'file' shows the name of the configuration
             file; 'edit' edits the configuration file
             in your preferred editor; 'convert' writes a new .toml
             configuration file with the same settings as the old
             .ini configuration file""",
        )
        return parser

    def do_config(self, cmdline: cmd2.Statement):
        """edit or show the location of the user configuration file"""
        args = self.parse_args(self.config_parser, cmdline.argv)

        if args.action == "file":
            self.poutput(self.config_file)
            self.exit_code = self.EXIT_SUCCESS
        elif args.action == "edit":
            self._config_edit()
        elif args.action == "convert":
            self._config_convert()

    def help_config(self):
        """Show help for the 'config' command"""
        self.show_help_from(self.config_parser)

    def _config_edit(self):
        """
        Open the configuration file in an editor, and reload the configuration when the
        editor exits.
        """
        if not self.editor:
            self.perror("no editor: use 'set editor = \"{path}\"' to specify one")
            self.exit_code = self.EXIT_ERROR
            return

        if self.config_file:
            # ensure the configuration directory exists
            configdir = self.config_file.parent
            if not configdir.exists():  # pragma: nocover
                configdir.mkdir(parents=True, exist_ok=True)

            # go edit the file
            cmd = f'"{self.editor}" "{self.config_file}"'
            self.pfeedback(f"executing {cmd}")
            os.system(cmd)

            # read it back in and apply it
            self.pfeedback("reloading configuration file")
            self.load_config()
            self.exit_code = self.EXIT_SUCCESS
        else:
            self.perror("could not figure out where configuration file should be")
            self.exit_code = self.EXIT_ERROR

    def _config_convert(self):
        """
        Convert the old .ini based configuration file into the new .toml
        based one.

        The .ini file _must_ exist and the .toml file _must not_ exist in order
        for this to do anything.
        """
        if self.config_file and self.config_file.exists():
            self.pfeedback(
                "configuration file exists: cowardly refusing to overwrite it"
            )
            self.exit_code = self.EXIT_ERROR
            return

        if self.config_file_old and not self.config_file_old.exists():
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

    def do_show(self, cmdline: cmd2.Statement):
        """Override cmd2 builtin show command to be invalid"""
        self.default(cmdline)

    @property
    def settings_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the settings command."""
        parser = argparse.ArgumentParser(
            prog="settings",
            description=self.do_settings.__doc__,
            formatter_class=RichHelpFormatter,
        )
        parser.add_argument(
            "setting",
            nargs="?",
            help="""name of the setting to show the value for;
             if omitted show the values of all settings""",
        )
        return parser

    def do_settings(self, cmdline: cmd2.Statement):
        """display program settings"""
        args = self.parse_args(self.settings_parser, cmdline.argv)

        if args.setting and args.setting not in self.settables:
            self.perror(f"unknown setting: '{args.setting}'")
            self.exit_code = self.EXIT_ERROR
            return

        # create a table with the desired output, we use this so the
        # comments line up nicely
        otable = rich.table.Table(
            show_edge=False,
            box=None,
            padding=(0, 3, 0, 0),
            show_header=False,
        )
        # for the setting and it's value
        otable.add_column(no_wrap=True)
        # for the comment which contains the description of the setting
        otable.add_column(no_wrap=True)

        for setting in sorted(self.settables):
            if (not args.setting) or (setting == args.setting):
                styled_setting = rich.text.Text(setting, style="tm.setting.name")
                styled_setting += " "
                styled_setting += rich.text.Text("=", style="tm.setting.equals")
                styled_setting += " "

                # create a tomlkit table so we can have tomlkit worry about
                # how render our python setting values as valid toml
                ttable = tomlkit.table()
                ttable.add(setting, getattr(self, setting))
                # now dump the table and peel off everything after
                # the first equal sign for the value
                # this breaks on quoted keys that contain and equals sign
                # but that shouldn't happen much
                value = tomlkit.dumps(ttable).split("=", 1)[1].strip()

                typ = type(getattr(self, setting))
                styled_value = value
                if typ == bool:
                    styled_value = rich.text.Text(value, style="tm.setting.bool")
                elif typ == str:
                    styled_value = rich.text.Text(value, style="tm.setting.string")
                elif typ == float:
                    styled_value = rich.text.Text(value, style="tm.setting.float")
                # we have no integer settings, so no way to test this, but it's
                # here for the future
                # elif typ == int:
                #    styled_value = rich.text.Text(value, style="tm.setting.int")

                styled_setting += styled_value
                styled_comment = rich.text.Text(
                    f"# {self.settables[setting].description}",
                    style="tm.setting.comment",
                )
                otable.add_row(
                    styled_setting,
                    styled_comment,
                )

        self.console.print(otable)
        self.exit_code = self.EXIT_SUCCESS

    def help_settings(self):
        """Show help for the 'settings' command"""
        self.show_help_from(self.settings_parser)

    @property
    def set_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the set command."""
        # we don't actually parse input with this argument parser
        # because it strips quotes off of the value, which we need
        # to remain in place so they will be valid toml syntax
        # we do use this argument parser to render help
        desc = """\
            change a program setting

            The syntax must be valid TOML, just like the config file. Here's some
            examples:

              tomcat-manager> set theme = "default-dark"
              tomcat-manager> set timing = true
              tomcat-manager> set timeout = 5.0
              tomcat-manager> set prompt = "tm> "
            """
        parser = argparse.ArgumentParser(
            prog="set",
            description=textwrap.dedent(desc),
            formatter_class=RawDescriptionRichHelpFormatter,
        )
        parser.add_argument(
            "setting",
            help="the name of the setting",
        )
        parser.add_argument(
            "equals",
            help="assignment operator",
            metavar="=",
        )
        parser.add_argument(
            "value",
            help="the value for the setting ",
        )
        return parser

    def do_set(self, args: cmd2.Statement):
        """change a program setting"""
        # we don't parse the input with self.set_parser() because
        # argparse.ArgumentParser.parse_args() swallows the quotes around
        # quoted arguments and we need those quotes to make valid TOML.
        if args:
            # so we have to check manually for help flags
            if args.arg_list[0] == "-h" or args.arg_list[0] == "--help":
                self.help_set()
                return

            try:
                # we need to use args.raw because args and arg.arg_list
                # have had all the quotation marks processed, which can
                # mess with our input -> TOML processing.
                # so we use args.raw and get rid of the "set " at the
                # beginning. TOML is tolerant of whitespace, so the
                # rest should be fine
                tomlstr = args.raw.replace("set ", "", 1)
                setting_string = f"[settings]\n{tomlstr}"
                config = tomlkit.loads(setting_string)

                for param_name in config["settings"]:
                    if param_name in self.settables:
                        self._change_setting(param_name, config["settings"][param_name])
                        self.exit_code = self.EXIT_SUCCESS
                    else:
                        self.perror(f"unknown setting: '{param_name}'")
                        self.exit_code = self.EXIT_ERROR
            except tomlkit.exceptions.TOMLKitError:
                self.perror(
                    "invalid syntax: use 'help set' to view syntax and examples"
                )
                self.exit_code = self.EXIT_ERROR
            except ValueError as err:
                # this could be thrown by self._change_setting if we try to set a string
                # value to a boolean parameter
                if self.debug:
                    self.perror(None)
                else:
                    self.perror(str(err))
                self.exit_code = self.EXIT_ERROR
        else:
            self.do_settings(args)

    def help_set(self):
        """Show help for the 'set' command"""
        self.show_help_from(self.set_parser)

    def _build_theme_parsers(self) -> Dict:
        """Construct all the argument parsers for the theme command."""
        main_parser = argparse.ArgumentParser(
            prog="theme",
            description="manage themes",
            formatter_class=RichHelpFormatter,
        )
        main_subparsers = main_parser.add_subparsers(
            dest="action",
            required=True,
            metavar="action",
        )

        # list available themes
        list_parser = main_subparsers.add_parser(
            "list",
            description="list all themes",
            help="list all themes",
            formatter_class=main_parser.formatter_class,
        )
        list_parser.set_defaults(func=self.theme_list)

        # clone a built-in theme
        clone_parser = main_subparsers.add_parser(
            "clone",
            description="clone a theme from the gallery or from one of the built-in themes",
            help="clone a theme from the gallery or from one of the built-in themes",
            formatter_class=main_parser.formatter_class,
        )
        clone_parser.set_defaults(func=self.theme_clone)
        clone_parser.add_argument(
            "name",
            help="name of the gallery or built-in theme to clone to user theme directory",
        )
        clone_parser.add_argument(
            "new_name", nargs="?", default="", help="new name of the theme"
        )

        # edit a user theme
        edit_parser = main_subparsers.add_parser(
            "edit",
            description="edit a user theme",
            help="edit a user theme",
            formatter_class=main_parser.formatter_class,
        )
        edit_parser.set_defaults(func=self.theme_edit)
        edit_parser.add_argument(
            "name", nargs="?", default="", help="name of theme to edit"
        )

        # create a new user theme
        create_parser = main_subparsers.add_parser(
            "create",
            description="create a new user theme",
            help="create a new user theme",
            formatter_class=main_parser.formatter_class,
        )
        create_parser.set_defaults(func=self.theme_create)
        create_parser.add_argument(
            "name",
            help="name for the new theme",
        )

        # delete a user theme
        delete_parser = main_subparsers.add_parser(
            "delete",
            description="delete a user theme",
            help="delete a user theme",
            formatter_class=main_parser.formatter_class,
        )
        delete_parser.set_defaults(func=self.theme_delete)
        delete_parser.add_argument(
            "name",
            help="name of the theme to delete",
        )
        delete_parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            help="don't prompt for confirmation before deleting",
        )

        # dir or directory
        dir_parser = main_subparsers.add_parser(
            "dir",
            description="show the theme directory",
            help="show the theme directory",
            formatter_class=main_parser.formatter_class,
        )
        dir_parser.set_defaults(func=self.theme_dir)

        # package all the parsers into a dictionary
        parsers = {}
        parsers["theme"] = main_parser
        parsers["list"] = list_parser
        parsers["clone"] = clone_parser
        parsers["edit"] = edit_parser
        parsers["create"] = create_parser
        parsers["delete"] = delete_parser
        parsers["dir"] = dir_parser
        return parsers

    @property
    def theme_parser(self) -> argparse.ArgumentParser:
        """Get the main argument parser for the theme command."""
        parsers = self._build_theme_parsers()
        return parsers["theme"]

    def do_theme(self, cmdline: cmd2.Statement):
        """manage themes"""
        args = self.parse_args(self.theme_parser, cmdline.argv)
        args.func(args)

    def theme_dir(self, args: argparse.Namespace):
        """show the theme directory"""
        self.poutput(self.user_theme_dir)
        self.exit_code = self.EXIT_SUCCESS

    # pylint: disable=too-many-branches,
    def theme_list(self, args: argparse.Namespace):
        """list all available themes"""
        gallery_themes = []
        with self._progressfactory("retrieving themes from gallery"):
            response = requests.get(
                f"{self.THEME_URL}/themes.toml",
                timeout=self.timeout,
            )
        if response.status_code == 200:
            gallery_dir = tomlkit.loads(response.text)
            for theme_name in gallery_dir:
                theme = Theme(
                    location=ThemeLocation.GALLERY,
                    file=pathlib.Path(gallery_dir[theme_name]["file"]),
                    description=gallery_dir[theme_name]["description"],
                )
                gallery_themes.append(theme)

        if gallery_themes:
            gallery_table = rich.table.Table(
                show_edge=False,
                box=None,
                padding=(0, 3, 0, 0),
                show_header=False,
            )
            gallery_table.add_column("Name")
            gallery_table.add_column("Description")
            for theme in gallery_themes:
                gallery_table.add_row(
                    rich.text.Text(theme.name, style="tm.theme.name"), theme.description
                )
            self.console.print("Gallery Themes", style="tm.theme.category")
            self.console.print("─" * 72, style="tm.theme.border")
            self.console.print(gallery_table)

        # built-in themes
        user_themes = {}
        user_table = rich.table.Table(
            show_edge=False,
            box=None,
            padding=(0, 3, 0, 0),
            show_header=False,
        )
        user_table.add_column("Name")
        user_table.add_column("Description")
        # add the built-in themes
        for path in importlib_resources.files("tomcatmanager.themes").iterdir():
            if path.suffix == ".toml":
                # go read the theme in to get the description
                tdesc = ""
                try:
                    with path.open("r", encoding="utf-8") as theme_fobj:
                        theme_def = tomlkit.load(theme_fobj)
                        tdesc = theme_def["description"]
                except OSError:
                    # this really shouldn't happen so much for the built-in themes
                    # but if it doesn, don't show it in the list
                    continue
                except tomlkit.exceptions.TOMLKitError:
                    # this really shouldnt' happen either, because we should ship
                    # valid built-in themes. But if it does, skipt it because
                    # the user can't load it and they can't edit it
                    continue
                theme = Theme(
                    location=ThemeLocation.BUILTIN,
                    file=pathlib.Path(path.name),
                    description=tdesc,
                )
                user_themes[theme.name] = theme
        # add the user themes
        if self.user_theme_dir.exists():
            for path in self.user_theme_dir.iterdir():
                if path.suffix == ".toml":
                    tdesc = ""
                    try:
                        with path.open("r", encoding="utf-8") as theme_fobj:
                            theme_def = tomlkit.load(theme_fobj)
                            tdesc = theme_def["description"]
                    except OSError:
                        # file couldn't be opened, or an error occured reading
                        # it. best not show this one in the list, so we skip over it
                        continue
                    except tomlkit.exceptions.TOMLKitError:
                        # badly formed toml, or no description field
                        # but the file exists, so show it in the list but
                        # with no description
                        pass
                    theme = Theme(
                        location=ThemeLocation.USER,
                        file=pathlib.Path(path.name),
                        description=tdesc,
                    )
                    user_themes[theme.name] = theme

        have_builtin = False
        for theme in list(user_themes.values()):
            if theme.location == ThemeLocation.BUILTIN:
                user_table.add_row(
                    rich.text.Text(f"{theme.name}*", style="tm.theme.name"),
                    theme.description,
                )
                have_builtin = True
            else:
                user_table.add_row(
                    rich.text.Text(theme.name, style="tm.theme.name"), theme.description
                )
        self.console.print("")
        self.console.print("User Themes", style="tm.theme.category")
        self.console.print("─" * 72, style="tm.theme.border")
        if user_themes:
            self.console.print(user_table)
        else:
            self.console.print("No built-in or user themes available.")
        if have_builtin:
            self.console.print()
            self.console.print("'*' indicates a read-only built-in theme.")
            self.console.print(
                "Make your own copy of a built-in or gallery theme with 'theme clone'."
            )
            self.console.print(
                "You can then edit your copy of the theme with 'theme edit'."
            )

        self.exit_code = self.EXIT_SUCCESS

    def theme_clone(self, args: argparse.Namespace):
        """clone a gallery theme to the user theme directory"""
        # get the theme we are cloning into a string.
        # since the network request has to fetch the theme
        # to see if it exists, we just do it all in one step.

        # the online theme gallery can override the built-in themes, so check
        # there first
        theme_str = None
        with self._progressfactory("retrieving themes from gallery"):
            response = requests.get(
                f"{self.THEME_URL}/themes/{args.name}.toml",
                timeout=self.timeout,
            )
        if response.status_code == 200:
            theme_str = response.text
        else:
            self.pfeedback(f"theme '{args.name}' not found in gallery")

        if not theme_str:
            # go see if it's a built-in theme
            path = importlib_resources.files("tomcatmanager.themes").joinpath(
                f"{args.name}.toml"
            )
            try:
                with path.open("r", encoding="utf-8") as theme_fobj:
                    theme_str = theme_fobj.read()
            except FileNotFoundError:
                # swallow this error silently
                # it's neither in the gallery or built-in
                self.pfeedback(f"theme '{args.name}' is not a built-in theme")

        if not theme_str:
            self.perror(f"unknown theme: '{args.name}'")
            self.exit_code = self.EXIT_ERROR
            return

        # see if new theme already exists, error message if it does
        new_name = args.new_name
        if new_name == "":
            new_name = args.name
        new_path = self.user_theme_dir / f"{new_name}.toml"
        if new_path.is_file():
            self.perror(f"clone aborted: '{new_name}' is already a user theme")
            self.exit_code = self.EXIT_ERROR
            return

        # copy theme to user theme dir
        self.pfeedback(f"cloning '{args.name}' to user theme '{new_name}'")
        self.ensure_user_theme_dir()
        with new_path.open("w", encoding="utf-8") as fobj:
            # shutil.copy(from_path, new_path)
            fobj.write(theme_str)
        self.exit_code = self.EXIT_SUCCESS
        return

    def theme_edit(self, args: argparse.Namespace):
        """edit a user theme file"""

        if not self.editor:
            self.perror("no editor: use 'set editor = \"{path}\"' to specify one")
            self.exit_code = self.EXIT_ERROR
            return

        # if args.name is empty, try the name of the current theme
        if args.name:
            name = args.name
        else:
            if self.theme:
                self.pfeedback(f"no theme given, editing current theme '{self.theme}'")
                name = self.theme
            else:
                self.perror("syntax error: no theme given")
                self.exit_code = self.EXIT_ERROR
                return

        # get the file to edit
        location, theme_file = self._resolve_theme(name)
        if location == ThemeLocation.BUILTIN:
            # this means no user theme with this name exists, but a builtin one does
            self.pfeedback(f"built in theme: '{name}'")
            self.pfeedback(f'use "theme clone {name}" to make an editable user theme')
            self.perror(f"theme is not editable: '{name}'")
            self.exit_code = self.EXIT_ERROR
            return
        if location is None:
            self.perror(f"unknown theme: '{name}'")
            self.exit_code = self.EXIT_ERROR
            return

        # go edit the file
        cmd = f'"{self.editor}" "{theme_file}"'
        self.pfeedback(f"executing {cmd}")
        os.system(cmd)

        # reapply the theme if necessary
        if self.theme == name:
            self.pfeedback(f"reloading theme: '{self.theme}'")
            if not self._apply_theme(name):
                self.exit_code = self.EXIT_ERROR
                return

        self.exit_code = self.EXIT_SUCCESS
        return

    def theme_create(self, args: argparse.Namespace):
        """create a user theme file from a template"""

        # see if requested new name already exists, error message if it does
        name = args.name
        new_path = self.user_theme_dir / f"{name}.toml"
        if new_path.is_file():
            self.perror(f"create aborted: '{name}' is already a user theme")
            self.exit_code = self.EXIT_ERROR
            return

        try:
            template_path = importlib_resources.files(
                "tomcatmanager.templates"
            ).joinpath("theme.toml")
            self.pfeedback(f"copying theme template to '{name}'")
            self.ensure_user_theme_dir()
            shutil.copy(template_path, new_path)
            self.exit_code = self.EXIT_SUCCESS
        except FileNotFoundError:
            with open(new_path, "w", encoding="utf-8") as outfile:
                outfile.write("#\n# tomcat-manager theme\n")
                self.exit_code = self.EXIT_SUCCESS
        return

    def theme_delete(self, args: argparse.Namespace):
        """delete a user theme"""
        name = args.name
        path = self.user_theme_dir / f"{name}.toml"

        if not path.is_file():
            self.perror(f"unknown theme: '{name}'")
            self.exit_code = self.EXIT_ERROR
            return

        if not args.force:
            confirm = input(f"Type 'y' or 'yes' to delete theme '{name}': ")
            if confirm not in ["y", "yes"]:
                self.perror("no confirmation: theme not deleted")
                self.exit_code = self.EXIT_ERROR
                return

        path.unlink(missing_ok=True)
        self.pfeedback(f"theme deleted: '{name}'")
        self.exit_code = self.EXIT_SUCCESS
        return

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

    @property
    def user_theme_dir(self) -> pathlib.Path:
        """
        The directory containing user theme files.

        tomcatmanager includes some themes as embedded resources which are not
        user editable. Putting theme files in this directory allows a user to
        create their own themes or override any of the included themes.

        :return: The full path to the directory containing user theme files.
                 This does not ensure the directory exists. Returns None if
                 self.appdirs has not been defined.
        """
        if self.appdirs:
            return pathlib.Path(self.appdirs.user_config_dir).resolve() / "themes"
        return None

    def ensure_user_theme_dir(self):
        """Create the user theme directory if it doesn't exist.

        throws an exception if the directory doesn't exist and we can't create it
        """
        if not self.user_theme_dir.exists():  # pragma: nocover
            self.user_theme_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self):
        """Open and parse the user config file and set self.config."""
        config = tomlkit.loads("")
        if self.config_file is not None:
            try:
                with open(self.config_file, "r", encoding="utf-8") as fobj:
                    config = tomlkit.loads(fobj.read())
            except tomlkit.exceptions.TOMLKitError as err:
                self.perror(f"error loading configuration file: {err}")
            except FileNotFoundError:
                pass

        # either we don't have a config file, or we were able to load it
        # now we can set all settings to their default values
        self._set_defaults()

        # and go process the settings we found in the config file
        first_error = True
        try:
            settings = config["settings"]
            for key in settings:
                try:
                    self._change_setting(key, settings[key])
                except ValueError as err:
                    # could be the setting name, or the setting value
                    if first_error:
                        self.perror(
                            "while loading the configuration file the following errors occured:"
                        )
                        first_error = False
                    self.perror(err)
        except tomlkit.exceptions.NonExistentKey:
            # we don't have a settings section, so there are no settings to load
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
        except KeyError as err:
            raise ValueError(f"unknown setting: {param_name}") from err
        except ValueError as err:
            raise ValueError(f"error while trying to set {param_name}: {err}") from err

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
    @property
    def connect_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the connect command."""

        # yes there are embedded spaces and linefeeds in this string
        # use markup using RichHelpFormatter native styles, which we keep
        # updated according to the styles from our current theme
        # we also have to escape open brackets so they don't get interpreted
        # as markup by RichHelpFormatter
        usagestr = (
            r"%(prog)s [argparse.args]\[-h][/]"
            "\n"
            r"       %(prog)s [argparse.args]config_name[/] [argparse.args]\[OPTIONS][/]"
            "\n"
            r"       %(prog)s [argparse.args]url[/] [argparse.args]\[user][/]"
            r" [argparse.args]\[password][/] [argparse.args]\[OPTIONS][/]"
            "\n"
        )

        parser = argparse.ArgumentParser(
            prog="connect",
            description=self.do_connect.__doc__,
            usage=usagestr,
            epilog="""If you specify a user and no password, you will be prompted for the
                password.""",
            formatter_class=RichHelpFormatter,
        )
        parser.add_argument(
            "config_name",
            nargs="?",
            help="a section from the config file which contains at least a url",
        )
        parser.add_argument(
            "url",
            nargs="?",
            help="the url where the tomcat manager web app is located",
        )
        parser.add_argument(
            "user",
            nargs="?",
            help="optional user to use for authentication",
        )
        parser.add_argument(
            "password",
            nargs="?",
            help="optional password to use for authentication",
        )
        parser.add_argument(
            "--cert",
            action="store",
            help="""path to certificate for client side authentication;
            file can include private key, in which case --key is unnecessary""",
        )
        parser.add_argument(
            "--key",
            action="store",
            help="path to private key for client side authentication",
        )
        parser.add_argument(
            "--cacert",
            action="store",
            help="""path to certificate authority bundle or directory used to
            validate server SSL/TLS certificate""",
        )
        parser.add_argument(
            "--noverify",
            # store_true makes the default False, aka default is to verify
            # server certificates
            action="store_true",
            help="don't validate server SSL certificates, overrides --cacert",
        )
        return parser

    # pylint: disable=too-many-branches, too-many-statements
    def do_connect(self, cmdline: cmd2.Statement):
        """connect to a tomcat manager instance"""
        # define some variables that we will either fill from a server definition
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

        if not server:
            self.help_connect()
            self.exit_code = self.EXIT_USAGE
            return

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

        try:
            with self._progressfactory("connecting"):
                r = self.tomcat.connect(url, user, password, verify=verify, cert=cert)

            if r.ok:
                self.pfeedback(self._which_server())
                if r.server_info.tomcat_version:
                    self.pfeedback(f"tomcat version: {r.server_info.tomcat_version}")
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
        """Show help for the 'connect' command."""
        self.show_help_from(self.connect_parser)

    @property
    def which_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the which command."""
        parser = argparse.ArgumentParser(
            prog="which",
            description=self.do_which.__doc__,
            formatter_class=RichHelpFormatter,
        )
        return parser

    def do_which(self, cmdline: cmd2.Statement):
        """show the url of the tomcat server you are connected to"""
        self.parse_args(self.which_parser, cmdline.argv)
        self.raise_if_not_connected()
        self.poutput(self._which_server())

    def help_which(self):
        """Show help for the 'which' command"""
        self.show_help_from(self.which_parser)

    @property
    def disconnect_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the disconnect command."""
        parser = argparse.ArgumentParser(
            prog="disconnect",
            description=self.do_disconnect.__doc__,
            formatter_class=RichHelpFormatter,
        )
        return parser

    def do_disconnect(self, cmdline: cmd2.Statement):
        """disconnect from a tomcat manager instance"""
        self.parse_args(self.disconnect_parser, cmdline.argv)
        self.tomcat.disconnect()
        self.pfeedback("disconnected")

    def help_disconnect(self):
        """Show help for the 'disconnect' command"""
        self.show_help_from(self.disconnect_parser)

    ###
    #
    # commands for managing applications
    #
    ###
    def deploy_local(self, args: argparse.Namespace, update: bool = False):
        """Deploy a local war file to the tomcat server"""
        warfile = pathlib.Path(args.warfile).expanduser()
        with open(warfile, "rb") as fileobj:
            apptag = self._apptag(args.path, args.version)
            if update:
                msg = f"redeploying {apptag}"
            else:
                msg = f"deploying {apptag}"
            self.docmd(
                msg,
                self.tomcat.deploy_localwar,
                args.path,
                fileobj,
                version=args.version,
                update=update,
            )

    def deploy_server(self, args: argparse.Namespace, update: bool = False):
        """Deploy a war file to the tomcat server"""
        apptag = self._apptag(args.path, args.version)
        if update:
            msg = f"redeploying {apptag}"
        else:
            msg = f"deploying {apptag}"
        self.docmd(
            msg,
            self.tomcat.deploy_serverwar,
            args.path,
            args.warfile,
            version=args.version,
            update=update,
        )

    def deploy_context(self, args: argparse.Namespace, update: bool = False):
        """Deploy a context xml file to the tomcat server"""
        apptag = self._apptag(args.path, args.version)
        if update:
            msg = f"redeploying {apptag}"
        else:
            msg = f"deploying {apptag}"
        self.docmd(
            msg,
            self.tomcat.deploy_servercontext,
            args.path,
            args.contextfile,
            warfile=args.warfile,
            version=args.version,
            update=update,
        )

    @property
    def deploy_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the deploy command."""
        (parser, _, _, _) = _deploy_parser(
            "deploy",
            self.do_deploy.__doc__,
            self.deploy_local,
            self.deploy_server,
            self.deploy_context,
        )
        return parser

    def do_deploy(self, cmdline: cmd2.Statement):
        """deploy an application to the tomcat server"""
        args = self.parse_args(self.deploy_parser, cmdline.argv)
        self.raise_if_not_connected()
        try:
            args.func(args, update=False)
        except AttributeError:  # pragma: nocover
            self.help_deploy()
            self.exit_code = self.EXIT_ERROR

    # we intercept do_help to display this help using a different approach.
    # leaving here, but commented out, so that if cmd2 gets
    # subcommand help support in the future, we can put this
    # back in.
    # def help_deploy(self):
    #     """Show help for the 'deploy' command"""
    #     self.show_help_from(self.deploy_parser)

    @property
    def redeploy_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the redeploy command."""
        (parser, _, _, _) = _deploy_parser(
            "redeploy",
            self.do_deploy.__doc__,
            self.deploy_local,
            self.deploy_server,
            self.deploy_context,
        )
        return parser

    def do_redeploy(self, cmdline: cmd2.Statement):
        """undeploy then deploy an application to the tomcat server"""
        args = self.parse_args(self.redeploy_parser, cmdline.argv)
        self.raise_if_not_connected()
        try:
            args.func(args, update=True)
        except AttributeError:  # pragma: nocover
            self.help_redeploy()
            self.exit_code = self.EXIT_ERROR

    # we intercept do_help to display this help using a different approach.
    # leaving here, but commented out, so that if cmd2 gets
    # subcommand help support in the future, we can put this
    # back in.
    # def help_redeploy(self):
    #     """Show help for the 'redeploy' command"""
    #     self.show_help_from(self.redeploy_parser)

    @property
    def undeploy_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the undeploy command"""
        return _path_version_parser("undeploy", self.do_undeploy.__doc__)

    def do_undeploy(self, cmdline: cmd2.Statement):
        """remove an application from the tomcat server"""
        args = self.parse_args(self.undeploy_parser, cmdline.argv)
        self.raise_if_not_connected()
        apptag = self._apptag(args.path, args.version)
        self.docmd(
            f"undeploying {apptag}", self.tomcat.undeploy, args.path, args.version
        )

    def help_undeploy(self):
        """Show help for the 'undeploy' command"""
        self.show_help_from(self.undeploy_parser)

    @property
    def start_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the start command."""
        return _path_version_parser("start", self.do_start.__doc__)

    def do_start(self, cmdline: cmd2.Statement):
        """start a deployed tomcat application that isn't running"""
        args = self.parse_args(self.start_parser, cmdline.argv)
        self.raise_if_not_connected()
        apptag = self._apptag(args.path, args.version)
        self.docmd(f"starting {apptag}", self.tomcat.start, args.path, args.version)

    def help_start(self):
        """Show help for the 'start' command"""
        self.show_help_from(self.start_parser)

    @property
    def stop_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the stop command."""
        return _path_version_parser("stop", self.do_stop.__doc__)

    def do_stop(self, cmdline: cmd2.Statement):
        """stop a tomcat application and leave it deployed on the server"""
        args = self.parse_args(self.stop_parser, cmdline.argv)
        self.raise_if_not_connected()
        apptag = self._apptag(args.path, args.version)
        self.docmd(f"stopping {apptag}", self.tomcat.stop, args.path, args.version)

    def help_stop(self):
        """Show help for the 'stop' command"""
        self.show_help_from(self.stop_parser)

    @property
    def reload_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the reload command."""
        return _path_version_parser("reload", self.do_reload.__doc__)

    def do_reload(self, cmdline: cmd2.Statement):
        """stop and start a tomcat application; synonym for restart"""
        args = self.parse_args(self.reload_parser, cmdline.argv)
        self.raise_if_not_connected()
        apptag = self._apptag(args.path, args.version)
        self.docmd(f"reloading {apptag}", self.tomcat.reload, args.path, args.version)

    def help_reload(self):
        """Show help for the 'reload' command"""
        self.show_help_from(self.reload_parser)

    @property
    def restart_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the restart command."""
        return _path_version_parser("restart", self.do_restart.__doc__)

    def do_restart(self, cmdline: cmd2.Statement):
        """stop and start a tomcat application"""
        self.do_reload(cmdline)

    def help_restart(self):
        """Show help for the 'restart' command"""
        self.show_help_from(self.restart_parser)

    @property
    def sessions_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the sessions command."""
        parser = argparse.ArgumentParser(
            prog="sessions",
            description=self.do_sessions.__doc__,
            formatter_class=RichHelpFormatter,
        )
        parser.add_argument(
            "path",
            help="the path part of the URL where the application is deployed",
        )
        parser.add_argument(
            "-v",
            "--version",
            help=(
                "optional version string of the application from which to show"
                " sessions; if the application was deployed with a version string,"
                " it must be specified in order to show sessions"
            ),
        )
        return parser

    def do_sessions(self, cmdline: cmd2.Statement):
        """show active sessions for a tomcat application"""
        args = self.parse_args(self.sessions_parser, cmdline.argv)
        self.raise_if_not_connected()
        r = self.docmd(None, self.tomcat.sessions, args.path, args.version)
        if r.ok:
            self.poutput(r.sessions)

    def help_sessions(self):
        """Show help for the 'sessions' command."""
        self.show_help_from(self.sessions_parser)

    @property
    def expire_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the expire command."""
        parser = argparse.ArgumentParser(
            prog="expire",
            description=self.do_expire.__doc__,
            formatter_class=RichHelpFormatter,
        )
        parser.add_argument(
            "-v",
            "--version",
            help=(
                "optional version string of the application from which to show"
                " sessions; if the application was deployed with a version string,"
                " it must be specified in order to show sessions"
            ),
        )
        parser.add_argument(
            "path",
            help="the path part of the URL where the application is deployed",
        )
        parser.add_argument(
            "idle",
            help="""expire sessions idle for more than this number of minutes; use
                0 to expire all sessions""",
        )
        return parser

    def do_expire(self, cmdline: cmd2.Statement):
        """expire idle sessions"""
        args = self.parse_args(self.expire_parser, cmdline.argv)
        self.raise_if_not_connected()
        r = self.docmd(None, self.tomcat.expire, args.path, args.version, args.idle)
        if r.ok:
            self.poutput(r.sessions)

    def help_expire(self):
        """Show help for the 'expire' command"""
        self.show_help_from(self.expire_parser)

    @property
    def list_parser(self) -> argparse.ArgumentParser:
        """Build the argument parser for the list command"""
        parser = argparse.ArgumentParser(
            prog="list",
            description=self.do_list.__doc__,
            formatter_class=RichHelpFormatter,
        )
        parser.add_argument(
            "-r",
            "--raw",
            action="store_true",
            help="show apps without formatting",
        )
        parser.add_argument(
            "-s",
            "--state",
            choices=["running", "stopped"],
            help="only show apps in a given state",
        )
        parser.add_argument(
            "-b",
            "--by",
            choices=["state", "path"],
            default="state",
            help="sort by state (default), or sort by path",
        )
        return parser

    def do_list(self, cmdline: cmd2.Statement):
        """show all installed tomcat applications"""
        args = self.parse_args(self.list_parser, cmdline.argv)
        self.raise_if_not_connected()

        response = self.docmd("listing applications", self.tomcat.list)
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
        """Show help for the 'list' command"""
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
    @property
    def serverinfo_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the serverinfo command."""
        return argparse.ArgumentParser(
            prog="serverinfo",
            description=self.do_serverinfo.__doc__,
            formatter_class=RichHelpFormatter,
        )

    def do_serverinfo(self, cmdline: cmd2.Statement):
        """show information about the tomcat server"""
        self.parse_args(self.serverinfo_parser, cmdline.argv)
        self.raise_if_not_connected()
        r = self.docmd("querying server", self.tomcat.server_info)
        if r.ok:
            self.poutput(r.result)

    def help_serverinfo(self):
        """Show help for the 'serverinfo' command"""
        self.show_help_from(self.serverinfo_parser)

    @property
    def status_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the status command."""
        return argparse.ArgumentParser(
            prog="status",
            description=self.do_status.__doc__,
            formatter_class=RichHelpFormatter,
        )

    def do_status(self, cmdline: cmd2.Statement):
        """show server status information in xml format"""
        self.parse_args(self.status_parser, cmdline.argv)
        self.raise_if_not_connected()
        r = self.docmd("querying server", self.tomcat.status_xml)
        root = xml.dom.minidom.parseString(r.status_xml)
        self.console.print(root.toprettyxml(indent="   ").strip())

    def help_status(self):
        """Show help for the 'status' command"""
        self.show_help_from(self.status_parser)

    @property
    def vminfo_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the vminfo command."""
        return argparse.ArgumentParser(
            prog="vminfo",
            description=self.do_vminfo.__doc__,
            formatter_class=RichHelpFormatter,
        )

    def do_vminfo(self, cmdline: cmd2.Statement):
        """show diagnostic information about the jvm"""
        self.parse_args(self.vminfo_parser, cmdline.argv)
        self.raise_if_not_connected()
        r = self.docmd("querying server", self.tomcat.vm_info)
        self.poutput(r.vm_info)

    def help_vminfo(self):
        """Show help for the 'vminfo' command"""
        self.show_help_from(self.vminfo_parser)

    @property
    def sslconnectorciphers_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the sslconnectorciphers command."""
        return argparse.ArgumentParser(
            prog="sslconnectorciphers",
            description=self.do_sslconnectorciphers.__doc__,
            formatter_class=RichHelpFormatter,
        )

    def do_sslconnectorciphers(self, cmdline: cmd2.Statement):
        """show SSL/TLS ciphers configured for each connector"""
        self.parse_args(self.sslconnectorciphers_parser, cmdline.argv)
        self.raise_if_not_connected()
        r = self.docmd("querying server", self.tomcat.ssl_connector_ciphers)
        self.poutput(r.ssl_connector_ciphers)

    def help_sslconnectorciphers(self):
        """Show help for the 'sslconnectorciphers' command"""
        self.show_help_from(self.sslconnectorciphers_parser)

    @property
    def sslconnectorcerts_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the sslconnectorcerts command."""
        return argparse.ArgumentParser(
            prog="sslconnectorcerts",
            description=self.do_sslconnectorcerts.__doc__,
            formatter_class=RichHelpFormatter,
        )

    def do_sslconnectorcerts(self, cmdline: cmd2.Statement):
        """show SSL/TLS certificate chain for each connector"""
        self.parse_args(self.sslconnectorcerts_parser, cmdline.argv)
        self.raise_if_not_connected()
        r = self.docmd("querying server", self.tomcat.ssl_connector_certs)
        self.poutput(r.ssl_connector_certs)

    def help_sslconnectorcerts(self):
        """Show help for the 'sslconnectorcerts' command"""
        self.show_help_from(self.sslconnectorcerts_parser)

    @property
    def sslconnectortrustedcerts_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the sslconnectortrustedcerts command."""
        return argparse.ArgumentParser(
            prog="sslconnectortrustedcerts",
            description=self.do_sslconnectortrustedcerts.__doc__,
            formatter_class=RichHelpFormatter,
        )

    def do_sslconnectortrustedcerts(self, cmdline: cmd2.Statement):
        """show SSL/TLS trusted certificates for each connector"""
        self.parse_args(self.sslconnectortrustedcerts_parser, cmdline.argv)
        self.raise_if_not_connected()
        r = self.docmd("querying server", self.tomcat.ssl_connector_trusted_certs)
        self.poutput(r.ssl_connector_trusted_certs)

    def help_sslconnectortrustedcerts(self):
        """Show help for the 'sslconnectortrustedcerts' command"""
        self.show_help_from(self.sslconnectortrustedcerts_parser)

    @property
    def sslreload_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the sslreload command."""
        parser = argparse.ArgumentParser(
            prog="sslreload",
            description=self.do_sslreload.__doc__,
            formatter_class=RichHelpFormatter,
        )
        parser.add_argument(
            "host_name",
            nargs="?",
            help="Optional host name to reload SSL/TLS certificates and keys for.",
        )
        return parser

    def do_sslreload(self, cmdline: cmd2.Statement):
        """reload SSL/TLS certificates and keys"""
        args = self.parse_args(self.sslreload_parser, cmdline.argv)
        self.raise_if_not_connected()
        self.docmd("reloading SSL/TLS", self.tomcat.ssl_reload, args.host_name)

    def help_sslreload(self):
        """Show help for the 'sslreload' command"""
        self.show_help_from(self.sslreload_parser)

    @property
    def threaddump_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the threaddump command"""
        return argparse.ArgumentParser(
            prog="threaddump",
            description=self.do_threaddump.__doc__,
            formatter_class=RichHelpFormatter,
        )

    def do_threaddump(self, cmdline: cmd2.Statement):
        """show a jvm thread dump"""
        self.parse_args(self.threaddump_parser, cmdline.argv)
        self.raise_if_not_connected()
        r = self.docmd("querying server", self.tomcat.thread_dump)
        self.poutput(r.thread_dump)

    def help_threaddump(self):
        """Show help for the 'threaddump' command"""
        self.show_help_from(self.threaddump_parser)

    @property
    def resources_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the resources command"""
        parser = argparse.ArgumentParser(
            prog="resources",
            description=self.do_resources.__doc__,
            formatter_class=RichHelpFormatter,
        )
        parser.add_argument(
            "class_name",
            nargs="?",
            help="optional fully qualified java class name of the resource type to show",
        )
        return parser

    def do_resources(self, cmdline: cmd2.Statement):
        """show global JNDI resources configured in tomcat"""
        args = self.parse_args(self.resources_parser, cmdline.argv)
        self.raise_if_not_connected()
        r = self.docmd("querying server", self.tomcat.resources, args.class_name)
        if r.resources:
            for resource, classname in iter(sorted(r.resources.items())):
                self.poutput(f"{resource}: {classname}")
        else:
            self.exit_code = self.EXIT_ERROR

    def help_resources(self):
        """Show help for the 'resources' command"""
        self.show_help_from(self.resources_parser)

    @property
    def findleakers_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the findleakers command."""
        return argparse.ArgumentParser(
            prog="findleakers",
            description=self.do_findleakers.__doc__,
            epilog="""WARNING: this triggers a full garbage collection on the server.
               Use with extreme caution on production systems.""",
            formatter_class=RichHelpFormatter,
        )

    def do_findleakers(self, cmdline: cmd2.Statement):
        """show tomcat applications that leak memory"""
        self.parse_args(self.findleakers_parser, cmdline.argv)
        self.raise_if_not_connected()
        r = self.docmd("finding memory leaks", self.tomcat.find_leakers)
        for leaker in r.leakers:
            self.poutput(leaker)

    def help_findleakers(self):
        """Show help for the 'findleakers' command"""
        self.show_help_from(self.findleakers_parser)

    ###
    #
    # miscellaneous user accessible commands
    #
    ###
    def do_exit(self, _):
        """exit the interactive command prompt"""
        self.exit_code = self.EXIT_SUCCESS
        return True

    def do_quit(self, cmdline: cmd2.Statement):
        """synonym for the 'exit' command"""
        return self.do_exit(cmdline)

    def do_eof(self, cmdline: cmd2.Statement):
        """exit on the end-of-file character"""
        return self.do_exit(cmdline)

    @property
    def version_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the version command."""
        parser = argparse.ArgumentParser(
            prog="version",
            description=self.do_version.__doc__,
            formatter_class=RichHelpFormatter,
        )
        return parser

    def do_version(self, cmdline: cmd2.Statement):
        """show the version number of this program"""
        self.parse_args(self.version_parser, cmdline.argv)
        self.poutput(tm.VERSION_STRING)

    def help_version(self):
        """Show help for the 'version' command"""
        self.show_help_from(self.version_parser)

    @property
    def exit_code_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the exit_code command."""
        exit_code_epilog = []
        exit_code_epilog.append("The codes have the following meanings:")
        for number, name in self.EXIT_CODES.items():
            exit_code_epilog.append(f"    {number:3}  {name}")

        return argparse.ArgumentParser(
            prog="exit_code",
            formatter_class=RawDescriptionRichHelpFormatter,
            description=self.do_exit_code.__doc__,
            epilog="\n".join(exit_code_epilog),
        )

    def do_exit_code(self, _):
        """show a number indicating the status of the previous command"""
        # we don't use exit_code_parser here because we don't want to generate
        # spurrious exit codes, i.e. if they have incorrect usage on the
        # exit_code command

        # don't set the exit code here, just show it
        self.poutput(self.exit_code)

    def help_exit_code(self):
        """Show help for the 'exit_code' command"""
        self.show_help_from(self.exit_code_parser)

    @property
    def license_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser for the license command."""
        parser = argparse.ArgumentParser(
            prog="license",
            description=self.do_license.__doc__,
            formatter_class=RichHelpFormatter,
        )
        return parser

    def do_license(self, cmdline: cmd2.Statement):
        """show the software license for this program"""
        self.parse_args(self.license_parser, cmdline.argv)
        mitlicense = textwrap.dedent(
            """\
            Copyright 2007 Jared Crapo

            Permission is hereby granted, free of charge, to any person obtaining a
            copy of this software and associated documentation files (the "Software"),
            to deal in the Software without restriction, including without limitation
            the rights to use, copy, modify, merge, publish, distribute, sublicense,
            and/or sell copies of the Software, and to permit persons to whom the
            Software is furnished to do so, subject to the following conditions:

            The above copyright notice and this permission notice shall be included in
            all copies or substantial portions of the Software.

            THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
            IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
            FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
            AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
            LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
            FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
            DEALINGS IN THE SOFTWARE.
            """
        )
        self.poutput(mitlicense)

    def help_license(self):
        """Show help for the 'license' command"""
        self.show_help_from(self.license_parser)


class ThemeLocation(enum.Enum):
    """An enumeration of the types of theme locations"""

    BUILTIN = "built-in"
    USER = "user"
    GALLERY = "gallery"


# pylint: disable=too-few-public-methods
class Theme:
    """Store information about a theme."""

    def __init__(self, **kwargs):
        """
        Initialize from the plain text response from a Tomcat server.

        :param result: the plain text from the server, minus the first
        line with the status info
        """
        self.file = kwargs.pop("file", None)
        self.description = kwargs.pop("description", None)
        self.location = kwargs.pop("location", None)

    @property
    def name(self):
        """name of the theme"""
        if self.file:
            return self.file.stem
        return None


# pylint: disable=too-many-ancestors
class EvaluatingConfigParser(configparser.ConfigParser):
    """Subclass of configparser.ConfigParser which evaluates values on get()."""

    # we need this as long as we have the ability to convert the old config
    # file format
    # pylint: disable=arguments-differ
    def get(self, section, option, **kwargs):
        val = super().get(section, option, **kwargs)
        if "'" in val or '"' in val:
            try:
                val = ast.literal_eval(val)
            except ValueError:  # pragma: nocover
                pass
        return val


def _to_bool(val: Any) -> bool:
    """Converts anything to a boolean based on its value.

    :param val: value being converted
    :return: boolean value expressed in the passed in value
    :raises: ValueError if the string can not be cast to a boolen

    This has to be able to accommodate TOML-style bools, as well as
    ini-style bools. That's why we lowercase the input before testing.
    """
    if isinstance(val, str):
        if val.lower() == "true":
            return True
        if val.lower() == "false":
            return False
        raise ValueError("syntax error: must be 'true' or 'false'")

    if isinstance(val, bool):
        return val

    return bool(val)


def _path_version_parser(cmdname: str, helpmsg: str) -> argparse.ArgumentParser:
    """Construct an argparser using the given parameters"""
    parser = argparse.ArgumentParser(
        prog=cmdname,
        description=helpmsg,
        formatter_class=RichHelpFormatter,
    )
    parser.add_argument(
        "-v",
        "--version",
        help=(
            f"optional version string of the application to"
            f" {cmdname}; if the application was deployed with"
            f" a version string, it must be specified in order to"
            f" {cmdname} the application"
        ),
    )
    path_help = "the path part of the URL where the application is deployed"
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
        formatter_class=RichHelpFormatter,
        epilog=f"type '{name} \\[deployment_method] -h' for more help",
    )
    deploy_subparsers = deploy_parser.add_subparsers(
        dest="method",
        required=True,
        metavar="deployment_method",
    )
    # local subparser
    deploy_local_parser = deploy_subparsers.add_parser(
        "local",
        description="transmit a war file from the local file system to the server",
        help="transmit a war file from the local file system to the server",
        formatter_class=deploy_parser.formatter_class,
    )
    deploy_local_parser.add_argument(
        "-v",
        "--version",
        help="version string to associate with this deployment",
    )
    deploy_local_parser.add_argument(
        "warfile",
        help=(
            "path on the local file system of a war file which will be"
            " transmitted to the server and deployed"
        ),
    )
    deploy_local_parser.add_argument(
        "path",
        help=(
            "context path, including the leading slash, on the server"
            " where the application will be available"
        ),
    )
    deploy_local_parser.set_defaults(func=localfunc)
    # server subparser
    deploy_server_parser = deploy_subparsers.add_parser(
        "server",
        description="deploy a war file from the server file system",
        help="deploy a war file from the server file system",
        formatter_class=deploy_parser.formatter_class,
    )
    deploy_server_parser.add_argument(
        "-v", "--version", help="version string to associate with this deployment"
    )
    deploy_server_parser.add_argument(
        "warfile",
        help=(
            "the java-style path (use slashes not backslashes) to the"
            " war file on the server file system; don't include 'file:'"
            " at the beginning"
        ),
    )
    deploy_server_parser.add_argument(
        "path",
        help=(
            "context path, including the leading slash, on the server"
            " where the application will be available"
        ),
    )
    deploy_server_parser.set_defaults(func=serverfunc)
    # context subparser
    deploy_context_parser = deploy_subparsers.add_parser(
        "context",
        description="deploy a context file from the server file system",
        help="deploy a context file from the server file system",
        formatter_class=deploy_parser.formatter_class,
    )
    deploy_context_parser.add_argument(
        "-v",
        "--version",
        help="version string to associate with this deployment",
    )
    deploy_context_parser.add_argument(
        "contextfile",
        help=(
            "the java-style path (use slashes not backslashes) to the"
            " war file on the server file system; don't include 'file:'"
            " at the beginning"
        ),
    )
    deploy_context_parser.add_argument(
        "warfile",
        nargs="?",
        help=(
            "the java-style path (use slashes not backslashes) to the"
            " war file on the server file system; don't include 'file:'"
            " at the beginning; overrides 'docBase' specified in the"
            " 'contextfile'"
        ),
    )
    deploy_context_parser.add_argument(
        "path",
        help=(
            "context path, including the leading slash, on the server where"
            " the warfile will be available; overrides the context path in"
            " 'contextfile'."
        ),
    )
    deploy_context_parser.set_defaults(func=contextfunc)
    return (
        deploy_parser,
        deploy_local_parser,
        deploy_server_parser,
        deploy_context_parser,
    )
