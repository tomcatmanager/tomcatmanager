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
tomcatmanager is a command line tool and python library for managing a Tomcat
server.

The most important class in the package is `TomcatManager`. This class connects
to a Tomcat Manager web application, allows you to run various commands, and
returns the responses to you as an instance of `TomcatManagerResponse`.

The command line program ``tomcat-manager`` is run by an instance of
`InteractiveTomcatManager`.
"""

from pkg_resources import get_distribution, DistributionNotFound

from .tomcat_manager import TomcatManager
from .models import TomcatError
from .models import status_codes
from .models import application_states
from .interactive_tomcat_manager import InteractiveTomcatManager

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    __version__ = 'unknown'
VERSION_STRING = '{} (works with Tomcat >= 7.0 and <= 9.0)'.format(__version__)
