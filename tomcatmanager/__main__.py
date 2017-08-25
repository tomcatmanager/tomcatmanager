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


#
# entry point for command line
def main(argv=None):
    """Entry point for 'tomcat-manager' command line program."""
    parser = argparse.ArgumentParser(
        description='Manage a tomcat server from the command line or an interactive shell'
    )
    # add epilog with additional usage info
    # should include something that says user, pass, and url all need to go together
    version_help = 'show the version information and exit'
    parser.add_argument('--version', action='version', version=tm.__version__,
                        help=version_help)
    user_help = 'user to use for authentication with the tomcat manager web application'
    parser.add_argument('-u', '--user',
                        help=user_help)
    password_help = 'password to use for authentication with the tomcat manager web application'
    parser.add_argument('-p', '--password',
                        help=password_help)
    debug_help = 'show additional debugging information while processing commands'
    parser.add_argument('--debug', action='store_true',
                        help=debug_help)
    url_help = 'url of the tomcat manager web application'
    parser.add_argument('manager_url', nargs='?',
                        help=url_help)
    command_help = 'optional command to run, if no command given, enter an interactive shell'
    parser.add_argument('command', nargs='?',
                        help=command_help)
    arg_help = 'optional arguments for command'
    parser.add_argument('arg', nargs='*',
                        help=arg_help)

    args = parser.parse_args(argv)
    if args.debug:
        print("--args=" + str(args), file=sys.stdout)

    itm = tm.InteractiveTomcatManager()
    itm._change_setting('debug', args.debug)

    if args.manager_url:
        # try and connect
        server_info = {'url': args.manager_url, 'user': '', 'password': ''}
        server_info['user'] = (args.user or '')
        if args.user:
            server_info['password'] = (args.password or '')
        itm.onecmd('connect {url} {user} {password}'.format_map(server_info))

        if args.command:
            if itm.exit_code == itm.exit_codes.success:
                # we connected successfully, go run the command
                itm.onecmd('{} {}'.format(args.command, ' '.join(args.arg)))
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
