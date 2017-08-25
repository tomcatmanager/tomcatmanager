.. :changelog:

Release History
===============

0.10.0 (2017-08-24)
-------------------

**New**

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

**Improved**

- `status` command now pretty prints the xml response

**Changed**

- `TomcatManager.__init__` no long accepts paramemeters: use `connect`
  instead
- `TomcatManager` methods which act on apps (`deploy`, `sessions`,
   `stop`, etc.) now throw exceptions if no path is specified. Previously
   they returned a response with `r.ok == False`


0.9.2 (2017-08-16)
------------------

**New**

- new TomcatManager.connect() method
- lots more documentation
- pytest now runs doctests

**Improved**

- version numbers now provided by `setuptools_scm`


0.9.1 (2017-08-10)
------------------

**Improved**

- New release to practice packaging and distribution


0.9.0 (2017-08-10)
------------------

**New**

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

**Improved**

- Switch from getopt to argparse
- Use `cmd2`, if available, instead of `cmd`
- Switch from `urllib` to `requests`

**Deprecated**

- Drop support for Python 3.3


Changes in 2014 and 2015
------------------------

- Remove methods deprecated in Python 3.4
- Add documentation to support Tomcat 7


0.4 (2013-07-07)
----------------

- Port to python 3, no support for python 2
- New `resources` command


0.3 (2013-01-02)
----------------

- Add code from private repo
