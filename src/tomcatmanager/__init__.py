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

The most important class in the package is :class:`.TomcatManager`. This class
connects to a Tomcat Manager web application, allows you to run various
commands, and returns the responses to you as an instance of
:class:`.TomcatManagerResponse`.

The interactive command line program ``tomcat-manager`` provided by this
package is an instance of ``InteractiveTomcatManager``. This command
line program uses the API documented here, but it not considered part of
the published API.
"""

try:
    # for python 3.8+
    import importlib.metadata as importlib_metadata
except ImportError:  # pragma: nocover
    # for python < 3.8
    import importlib_metadata

from .tomcat_manager import TomcatManager
from .models import (
    TomcatError,
    TomcatNotConnected,
    TomcatNotImplementedError,
    StatusCode,
    ApplicationState,
    TomcatMajorMinor,
)
from .interactive_tomcat_manager import InteractiveTomcatManager

try:
    __version__ = importlib_metadata.version(__name__)
except importlib_metadata.PackageNotFoundError:  # pragma: nocover
    __version__ = "unknown"
VERSION_STRING = "{} (works with Tomcat >= {} and <= {})".format(
    __version__,
    TomcatMajorMinor.lowest_supported().value,
    TomcatMajorMinor.highest_supported().value,
)
