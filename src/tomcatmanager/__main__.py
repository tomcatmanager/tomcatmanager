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
Entry point for 'tomcat-manager' command line program.
"""
import argparse
import sys

import tomcatmanager as tm

def _build_parser():
    """Build the argument parser"""
    parser = argparse.ArgumentParser(
        description='Manage a tomcat server from the command line or an interactive shell'
    )
    user_help = 'user to use for authentication with the tomcat manager web application'
    parser.add_argument('-u', '--user', help=user_help)

    password_help = 'password to use for authentication with the tomcat manager web application'
    parser.add_argument('-p', '--password', help=password_help)

    echo_help = 'echo the command into the output'
    parser.add_argument('-e', '--echo', action='store_true', help=echo_help)

    quiet_help = 'suppress all status output'
    parser.add_argument('-q', '--quiet',
                        action='store_true', help=quiet_help)

    status_help = 'send status information to stdout instead of stderr'
    parser.add_argument('-s', '--status-to-stdout',
                        action='store_true', help=status_help)

    debug_help = 'show additional debugging information while processing commands'
    parser.add_argument('-d', '--debug',
                        action='store_true', help=debug_help)

    version_help = 'show the version information and exit'
    parser.add_argument('-v', '--version', action='version',
                        version=tm.VERSION_STRING, help=version_help)

    url_help = 'url of the tomcat manager web application'
    parser.add_argument('manager_url', nargs='?',
                        help=url_help)

    command_help = 'optional command to run, if no command given, enter an interactive shell'
    parser.add_argument('command', nargs='?',
                        help=command_help)

    arg_help = 'optional arguments for command'
    parser.add_argument('command_args', nargs=argparse.REMAINDER,
                        help=arg_help)

    return parser

#
# entry point for command line
def main(argv=None):
    """Entry point for 'tomcat-manager' command line program."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.debug:
        print("--argv=" + str(argv), file=sys.stderr)
        print("--args=" + str(args), file=sys.stderr)

    itm = tm.InteractiveTomcatManager()

    # if we have command line switches, set those values
    # these override any user settings loaded from a config file
    if args.echo:
        itm.echo = True
    if args.quiet:
        itm.quiet = True
    if args.status_to_stdout:
        itm.status_to_stdout = True
    if args.debug:
        itm.debug = True

    if args.manager_url:
        # try and connect
        server_info = {'url': args.manager_url, 'user': '', 'password': ''}
        server_info['user'] = (args.user or '')
        if args.user:
            server_info['password'] = (args.password or '')
        itm.onecmd_plus_hooks('connect {url} {user} {password}'.format_map(server_info))

        if args.command:
            if itm.exit_code == itm.exit_codes.success:
                # we connected successfully, go run the command
                itm.onecmd_plus_hooks('{} {}'.format(args.command, ' '.join(args.command_args)))
        else:
            # we have no command, but we got a url, regardless of
            # whether the connect command worked or didn't, let's drop
            # into interactive mode
            itm.cmdloop()
    else:
        # we don't have a manager url, enter the interactive mode
        itm.cmdloop()
    return itm.exit_code


if __name__ == "__main__":
    sys.exit(main())
