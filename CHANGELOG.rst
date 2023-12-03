Changelog
=========

All notable changes to `tomcatmanager
<https://github.com/tomcatmanager/tomcatmanager>`__ are documented in this file.

This project uses `Semantic Versioning <http://semver.org/spec/v2.0.0.html>`_ and the
format of this file follows recommendations from `Keep a Changelog
<http://keepachangelog.com/en/1.1.0/>`_.

7.0.0 (2023-12-02)
------------------

Added
^^^^^

- Support for Python 3.12
- Support for themes in ``tomcat-manager``, which can produce styled and colored output

    - New ``theme`` setting to choose which theme to use
    - New command line option ``--theme`` to set theme from command line
    - New environment variable ``TOMCATMANAGER_THEME`` to set theme from environment
    - New ``theme`` command for users to list, create, edit, and delete themes
    - Theme gallery which shows themes from an online gallery. Themes can be added
      and updated in the gallery independent of ``tomcat-manager`` releases.
    - Two built-in themes, ``default-light``, and ``default-dark``
    - New command line option ``--theme-dir`` to show the full path to the user
      theme directory

- New command line option ``--noconfig`` to prevent the configuration file from
  being loading on startup
- New command line option ``--config-file`` to show the full path to the
  configuration file
- New command ``disconnect`` to disconnect from a Tomcat server
- New method `TomcatManager.disconnect()
  <https://tomcatmanager.readthedocs.io/en/stable/api/TomcatManager.html#tomcatmanager.tomcat_manager.TomcatManager.disconnect>`__

Changed
^^^^^^^

- Output from the ``settings`` command now matches the TOML format of the
  configuration file
- ``settings`` command now accepts input using TOML syntax
- Server shortcuts have been renamed to server definitions. There is no change to
  the functionality, only a change to the name.

Removed
^^^^^^^

- Drop support for Python 3.7 (EOL 27 June 2023)
- Removed allow_style setting
- Removed show command; settings does the same thing and is still available

Fixed
^^^^^

- ``config edit`` command now sets default values before reloading configuration


6.0.1 (2022-11-15)
------------------

Added
^^^^^

- Documentation for migrating to 6.x


Changed
^^^^^^^

- Improved documentation for `module dependency specification <https://tomcatmanager.readthedocs.io/en/stable/package.html#specifying-as-a-dependency>`_
- Improved documentation for `differences in Tomcat versions <https://tomcatmanager.readthedocs.io/en/stable/package.html#differences-in-tomcat-versions>`_


6.0.0 (2022-11-14)
------------------

Added
^^^^^

- Support for Python 3.11
- Support for Tomcat 10.1


Changed
^^^^^^^

- Change configuration file from ``ini`` format to ``toml`` format. See
  `Configuration File <https://tomcatmanager.readthedocs.io/en/stable/interactive.html#configuration-file>`_
  for more information.
- ``config_file`` attribute now contains a ``pathlib.Path`` object instead
  of a ``str`` for better cross-platform compatability
- ``history_file`` attribute now contains a ``pathlib.Path`` object instead
  of a ``str`` for better cross-platform compatability
- Switch to ``pyproject.toml`` from ``setup.py``. This has no impact on
  functionality, it's just a packaging change.

Removed
^^^^^^^

- Support for Tomcat 8.0 (EOL 30 June 2018)


5.0.0 (2021-11-19)
------------------

Added
^^^^^

- Support for Python 3.10
- Cross-reference links to Requests and standard library documentation

Removed
^^^^^^^

- Support for Python 3.6, which will not receive security fixes after
  2021-12-23. Python 3.6 should still work for now, but we no longer test
  against it.

Fixed
^^^^^

- `TomcatManager.is_connected()
  <https://tomcatmanager.readthedocs.io/en/stable/api/TomcatManager.html#tomcatmanager.tomcat_manager.TomcatManager.is_connected>`__
  now returns ``True`` or ``False`` instead of truthy or falsy values
- Fix interactive ``py`` and ``pyscript`` commands which were broken by upstream
  changes in cmd2 version 2.0


4.0.0 (2021-08-26)
------------------

Added
^^^^^

- Add ``py.typed`` file to make type annotations work properly per PEP 516
- Add documentation showing how to specify tomcatmanager as a dependency
  in your package

Removed
^^^^^^^

- Support for Tomcat 7, which is no longer supported or available for download

Fixed
^^^^^

- Fixed bug when parsing authentication credentials on the shell command line
  to ``tomcat-manager``


3.0.0 (2021-05-04)
------------------

Added
^^^^^

- Support for discovering and exposing the version of the Tomcat server we
  are connected to in the API. See `TomcatManager.connect()
  <https://tomcatmanager.readthedocs.io/en/stable/api/TomcatManager.html#tomcatmanager.tomcat_manager.TomcatManager.connect>`_,
  `TomcatManager.implements()
  <https://tomcatmanager.readthedocs.io/en/stable/api/TomcatManager.html#tomcatmanager.tomcat_manager.TomcatManager.implements>`_,
  and `TomcatManager.implemented_by()
  <https://tomcatmanager.readthedocs.io/en/stable/api/TomcatManager.html#tomcatmanager.tomcat_manager.TomcatManager.implemented_by>`_.
- `TomcatMajorMinor <https://tomcatmanager.readthedocs.io/en/stable/api/TomcatMajorMinor.html>`_
  enumeration for supported versions of Tomcat. Major and minor have the meaning
  defined at `https://semver.org/ <https://semver.org>`_.
- `TomcatManager.tomcat_major_minor
  <https://tomcatmanager.readthedocs.io/en/stable/api/TomcatManager.html#tomcatmanager.tomcat_manager.TomcatManager.tomcat_major_minor>`_
  attribute which contains one of the values from `TomcatMajorMinor`_
  representing the version of the Tomcat server we are connected to.
- Control server SSL/TLS certificate validation using the new ``verify`` parameter
  to `TomcatManager.connect()`_.
  Also available from the command-line and interactive mode using the ``--cacert``
  and ``--noverify`` options of the ``connect`` command.
- Client side SSL/TLS certificate authentication added to
  `TomcatManager.connect()`_
  via the ``cert`` parameter. Also available from the command line and interactive
  mode using the ``--cert`` and ``--key`` options of the ``connect`` command.
- Documentation explaining all
  `authentication <https://tomcatmanager.readthedocs.io/en/stable/authentication.html>`_
  approaches with configuration and usage examples.
- Documentation for
  `migrating from 2.x to 3.x
  <https://tomcatmanager.readthedocs.io/en/stable/api/migrating3.html>`_.


Changed
^^^^^^^
- `TomcatManager
  <https://tomcatmanager.readthedocs.io/en/stable/api/TomcatManager.html>`_
  methods raise `TomcatNotConnected
  <https://tomcatmanager.readthedocs.io/en/stable/api/TomcatNotConnected.html>`_ if
  called before `connect()
  <https://tomcatmanager.readthedocs.io/en/stable/api/TomcatManager.html#tomcatmanager.tomcat_manager.TomcatManager.connect>`_.
  Previously you got a `TomcatManagerResponse
  <https://tomcatmanager.readthedocs.io/en/stable/api/TomcatManagerResponse.html>`_
  and had to call `raise_for_status()
  <https://tomcatmanager.readthedocs.io/en/stable/api/TomcatManagerResponse.html#tomcatmanager.models.TomcatManagerResponse.raise_for_status>`_
  or check `ok
  <https://tomcatmanager.readthedocs.io/en/stable/api/TomcatManagerResponse.html#tomcatmanager.models.TomcatManagerResponse.ok>`_
  in order to determine that you weren't connected.
- `TomcatManager.url
  <https://tomcatmanager.readthedocs.io/en/stable/api/TomcatManager.html#tomcatmanager.tomcat_manager.TomcatManager.url>`_
  and `TomcatManager.user
  <https://tomcatmanager.readthedocs.io/en/stable/api/TomcatManager.html#tomcatmanager.tomcat_manager.TomcatManager.user>`_
  are now read-only properties set by `TomcatManager.connect()`_.
- `TomcatManager`_ methods raise `TomcatNotImplementedError
  <https://tomcatmanager.readthedocs.io/en/stable/api/TomcatNotImplementedError.html>`_
  if the server does not implement the requested capability. For example `ssl_reload()
  <https://tomcatmanager.readthedocs.io/en/stable/api/TomcatManager.html#tomcatmanager.tomcat_manager.TomcatManager.ssl_reload>`__
  is not implemented by Tomcat 7.0.x or 8.0.x, so if you are connected to a Tomcat 7.0.x
  server and call `ssl_reload()
  <https://tomcatmanager.readthedocs.io/en/stable/api/TomcatManager.html#tomcatmanager.tomcat_manager.TomcatManager.ssl_reload>`__,
  `TomcatNotImplementedError`_ will be raised.
- Timeouts were previously ``int`` only, now they can be ``float``
- The ``timeout`` parameter to `TomcatManager.connect()`_
  is now keyword only.


Fixed
^^^^^

- `TomcatManager.connect()`_ no longer erroneously sets the `url
  <https://tomcatmanager.readthedocs.io/en/stable/api/TomcatManager.html#tomcatmanager.tomcat_manager.TomcatManager.url>`_
  and `user <https://tomcatmanager.readthedocs.io/en/stable/api/TomcatManager.html#tomcatmanager.tomcat_manager.TomcatManager.user>`_
  attributes if an exception is raised.
- Allow ``--timeout=0`` from the command line if you want to wait forever for
  network operations.


2.0.0 (2021-03-26)
------------------

Added
^^^^^

- Support for Python 3.9
- Support for Tomcat 10
- New methods on TomcatManager: ``ssl_connector_certs()``,
  ``ssl_connector_trusted_certs()``, and ``ssl_reload()``
- New commands in ``tomcat-manager``: ``sslconnectorcerts``,
  ``sslconnectortrustedcerts`` and ``sslreload``
- Documentation for `migrating from 1.x to 2.x
  <https://tomcatmanager.readthedocs.io/en/stable/api/migrating2.html>`_

Changed
^^^^^^^

- ``TomcatApplication.state`` now contains an ``Enum`` instead of an
  ``AttrDict``
- The ``tomcatmanager.application_states`` dict has been replaced by the
  ``tomcatmanager.ApplicationState`` enum
- Timeouts can now be ``float`` instead of ``int``
- Improved documentation for network timeouts

Removed
^^^^^^^

- Support for Python 3.5, which as of 2020-09-13 no longer receives
  security updates
- Dependency on ``attrdict`` module, which has been archived


1.0.2 (2020-03-05)
------------------

Changed
^^^^^^^

- upstream ``cmd2`` library released v1.0.0. Now require ``cmd2>=1,<2``.

Fixed
^^^^^

- timeout command line and setting was not being honored


1.0.1 (2020-02-21)
------------------

Changed
^^^^^^^

- ``cmd2=0.10`` changed the way settings work. We now require that version or higher.


1.0.0 (2020-02-01)
------------------

Changed
^^^^^^^

- Switch documentation theme from ``alabaster`` to ``sphinx_rtd_theme``

Added
^^^^^

- Already have a setting to control network timeouts. Added a command line option
  ``--timeout`` to do the same, making it easier for modify for command-line only use.
- Adjustments for upstream changes in ``cmd2``. No longer pinned to
  ``cmd2=0.9.4``, but require ``cmd2>=0.9.14``.
- Add support for Python 3.8.
- Add documentation style checking using ``doc8``.

Removed
^^^^^^^

- Drop support for Python 3.4, which reached end-of-life on Mar 18, 2019.


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
- add ``config`` command which allows user to edit config file
- server shortcuts: save url, user, and password in config file
- ``which`` command to show which tomcat server you are connected to
- ``timeout`` setting for HTTP timeouts
- ``restart`` command as synonym for ``reload``
- Add tox for testing against multiple versions of python

Changed
^^^^^^^

- ``status`` command now pretty prints the xml response
- ``TomcatManager.__init__`` no long accepts paramemeters: use
  ``connect`` instead
- ``TomcatManager`` methods which act on apps (``deploy``, ``sessions``,
   ``stop``, etc.) now throw exceptions if no path is specified. Previously
   they returned a response with ``r.ok == False``


0.9.2 (2017-08-16)
------------------

Added
^^^^^

- new TomcatManager.connect() method
- lots more documentation
- pytest now runs doctests

Changed
^^^^^^^

- version numbers now provided by ``setuptools_scm``


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
- Add ``expire`` command
- Add ``vminfo`` command
- Add ``sslconnectorciphers`` command
- Add ``threaddump`` command
- Add ``findleaks`` command
- Add ``status`` command
- Unit tests using pytest
- Support Tomcat parallel deployment
- Real documentation using Sphinx
- Packaged to PyPI

Changed
^^^^^^^

- Switch from getopt to argparse
- Use ``cmd2``, if available, instead of ``cmd``
- Switch from ``urllib`` to ``requests``

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
