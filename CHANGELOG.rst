.. :changelog:

Changelog
=========
All notable changes to
`tomcatmanager <https://github.com/tomcatmanager/tomcatmanager>`_ will
be documented in this file.

The format is based on `Keep a Changelog <http://keepachangelog.com/en/1.0.0/>`_
and this project uses `Semantic Versioning <http://semver.org/spec/v2.0.0.html>`_.


0.14.0 (2019-05-16)
-------------------

Changed
^^^^^^^
- ``invoke clean.pycache`` is now ``invoke clean.bytecode``
- Run tests using python 3.7 on Appveyor and Travis
- Source code has been moved inside of ``src`` directory
- Pin cmd2 to version 0.9.4; newer versions break us badly

0.13.0 (2018-07-06)
-------------------

Added
^^^^^

- In the interactive ``tomcat-manager`` tool, the history of previously
  executed commands is now persistent across invocations of the program.
- Added common developer tasks to ``tasks.py``. To run these tasks, use the
  ``invoke`` command provided by `pyinvoke <http://www.pyinvoke.org/>`_.
- Tomcat 9.0.x officially supported. No material changes were required to
  gain this support, just validation via the test suite.
- Type hinting added for enhanced developer productivity in most IDE's
- Full support for Python 3.7

Changed
^^^^^^^

- ``ServerInfo.__init__()`` no longer accepts the result as a positional
  argument: it must be a keyword argument.

Fixed
^^^^^

- Test suite now runs several orders of magnitude faster. The 
  upstream `cmd2 <https://github.com/python-cmd2/cmd2>`_ used
  `pyparsing <https://sourceforge.net/projects/pyparsing/>`_ which
  was very slow. ``cmd2`` versions >= 0.9.0 use ``shlex`` to parse
  commands.


0.12.0 (2018-02-23)
-------------------

Added
^^^^^

- You can now deploy applications via a context xml file. A new
  interactive command ``deploy context`` and a new method
  ``deploy_servercontext()`` provide this capability.

Changed
^^^^^^^

- Better help messages in the interactive ``tomcat-manager`` tool
- ``deploy()`` has been replaced by three new methods: ``deploy_localwar()``,
  ``deploy_serverwar()``, and ``deploy_servercontext()``.
- Commands which use an optional version parameter now use a ``-v`` option
  to specify the version
- Most commands now have ``-h``/``--help`` options


0.11.0 (2017-09-06)
-------------------

Added
^^^^^

- New command line switches for ``tomcat-manager``: ``--quiet``, ``--echo``,
  ``--status_to_stdout``
- New setting ``status_prefix`` contains the string to emit prior to all
  status messages
- New class ``TomcatApplication``

Changed
^^^^^^^

- If we get an http redirect during ``TomcatManager.connect()``, save the new
  url so we don't have to re-traverse the redirect on every command.
- Interactive `list` command now can filter by application state, and has two
  sort options.
- ``TomcatManager._user`` is now ``TomcatManager.user``
- ``TomcatManager._url`` is now ``TomcatManager.url``
- ``TomcatManager.list()`` now returns a list of ``TomcatApplication`` objects
- Renamed ``tm.codes`` to ``tm.status_codes`` to clarify the purpose


0.10.0 (2017-08-24)
-------------------

Added
^^^^^

- CHANGELOG.rst
- documentation for interactive mode
- documentation for use from the shell command line
- read settings from a config file
- add `config` command which allows user to edit config file
- server shortcuts: save url, user, and password in config file
- `which` command to show which tomcat server you are connected to
- `timeout` setting for HTTP timeouts
- `restart` command as synonym for `reload`
- Add tox for testing against multiple versions of python

Changed
^^^^^^^

- `status` command now pretty prints the xml response
- `TomcatManager.__init__` no long accepts paramemeters: use `connect`
  instead
- `TomcatManager` methods which act on apps (`deploy`, `sessions`,
   `stop`, etc.) now throw exceptions if no path is specified. Previously
   they returned a response with `r.ok == False`


0.9.2 (2017-08-16)
------------------

Added
^^^^^

- new TomcatManager.connect() method
- lots more documentation
- pytest now runs doctests

Changed
^^^^^^^

- version numbers now provided by `setuptools_scm`


0.9.1 (2017-08-10)
------------------

Changed
^^^^^^^

- New release to practice packaging and distribution


0.9.0 (2017-08-10)
------------------

Added
^^^^^

- Converted from a single script to an installable python package
- Remove documentation for tomcat 6, which is no longer supported
- Add `expire` command
- Add `vminro` command
- Add `sslconnectorciphers` command
- Add `threaddump` command
- Add `findleaks` command
- Add `status` command
- Unit tests using pytest
- Support Tomcat parallel deployment
- Real documentation using Sphinx
- Packaged to PyPI

Changed
^^^^^^^

- Switch from getopt to argparse
- Use `cmd2`, if available, instead of `cmd`
- Switch from `urllib` to `requests`

Removed
^^^^^^^

- Drop support for Python 3.3


Changes in 2014 and 2015
------------------------

- Remove methods deprecated in Python 3.4
- Add documentation to support Tomcat 7


0.4 (2013-07-07)
----------------

Added
^^^^^

- Port to python 3
- New `resources` command

Removed
^^^^^^^
- Drop support for python 2

0.3 (2013-01-02)
----------------

Added
^^^^^

- Add code from private repo
