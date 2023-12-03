Contributing
============

Get Source Code
---------------

Clone the repo from github::

   $ git clone git@github.com:tomcatmanager/tomcatmanager.git


Create Python Environments
--------------------------

tomcatmanager uses `tox <https://tox.readthedocs.io/en/latest/>`_ to run the test
suite against multiple python versions. tox expects that when it runs ``python3.9`` it
will actually get a python from the 3.9.x series.

I recommend using `pyenv <https://github.com/pyenv/pyenv>`_ with the `pyenv-virtualenv
<https://github.com/pyenv/pyenv-virtualenv>`_ plugin to manage these various python
versions. If you are a Windows user, ``pyenv`` won't work for you, you'll probably
have to use `conda <https://conda.io/>`_.

This distribution includes a shell script ``build-pyenvs.sh`` which automates the
creation of these environments.

If you prefer to create these virtual envs by hand, do the following::

   $ cd tomcatmanager
   $ pyenv install 3.12.0
   $ pyenv virtualenv -p python3.12 3.12.0 tomcatmanager-3.12
   $ pyenv install 3.11.5
   $ pyenv virtualenv -p python3.11 3.11.5 tomcatmanager-3.11
   $ pyenv install 3.10.13
   $ pyenv virtualenv -p python3.10 3.10.13 tomcatmanager-3.10
   $ pyenv install 3.9.18
   $ pyenv virtualenv -p python3.9 3.9.18 tomcatmanager-3.9
   $ pyenv install 3.8.18
   $ pyenv virtualenv -p python3.8 3.8.18 tomcatmanager-3.8


Now set pyenv to make all five of those available at the same time::

   $ pyenv local tomcatmanager-3.12 tomcatmanager-3.11 tomcatmanager-3.10 tomcatmanager-3.9 tomcatmanager-3.8

Whether you ran the script, or did it by hand, you now have isolated virtualenvs for
each of the minor python versions. This table shows various python commands, the
version of python which will be executed, and the virtualenv it will utilize.

==============  =======  ==================
Command         python   virtualenv
==============  =======  ==================
``python``       3.12.0  tomcatmanager-3.12
``python3``      3.12.0  tomcatmanager-3.12
``python3.12``   3.12.0  tomcatmanager-3.12
``python3.11``   3.11.5  tomcatmanager-3.11
``python3.10``  3.10.13  tomcatmanager-3.10
``python3.9``    3.9.18  tomcatmanager-3.9
``python3.8``    3.8.18  tomcatmanager-3.8
``pip``          3.11.5  tomcatmanager-3.11
``pip3``         3.11.5  tomcatmanager-3.11
``pip3.11``      3.11.5  tomcatmanager-3.11
``pip3.10``     3.10.13  tomcatmanager-3.10
``pip3.9``       3.9.18  tomcatmanager-3.9
``pip3.8``       3.8.18  tomcatmanager-3.8
==============  =======  ==================


Install Dependencies
--------------------

Now install all the development dependencies::

   $ pip install -e .[dev]

This installs the tomcatmanager package "in-place", so the package points to the
source code instead of copying files to the python ``site-packages`` folder.

All the dependencies now have been installed in the ``tomcatmanager-3.12`` virtualenv.
If you want to work in other virtualenvs, you'll need to manually select it, and
install again::

   $ pyenv shell tomcatmanager-3.10
   $ pip install -e .[dev]


Branches, Tags, and Versions
----------------------------

This project uses a simplified version of the `git flow branching strategy
<http://nvie.com/posts/a-successful-git-branching-model/>`_. We don't use release
branches, and we generally don't do hotfixes, so we don't have any of those branches
either. The ``main`` branch always contains the latest release of the code uploaded to
PyPI, with a tag for the version number of that release.

The ``develop`` branch is where all the action occurs. Feature branches are welcome.
When it's time for a release, we merge ``develop`` into ``main``.

This project uses `semantic versioning <https://semver.org/>`_.

When this library adds support for a new version of Tomcat or Python, we increment the
minor version number. However, if support for these new versions requires API changes
incompatible with prior releases of this software, then we increment the major version
number.

When this library drops support for a version of Tomcat or Python, we increment the
major version number. For example, when this project dropped support for Python 3.6,
we released that version as 5.0.0 instead of 4.1.0, even though there were no
incompatible API changes.

These versioning rules were chosen so that if you are using this library against a
single version of Tomcat, and you specify your ``pyproject.toml`` dependency rules
like::

   [project]
   dependencies = [
    "tomcatmanager>=4,<5"
   ]

you won't have to worry about a future release of this software breaking your
setup.


Invoking Common Development Tasks
---------------------------------

This project uses many other python modules for various development tasks, including
testing, rendering documentation, and building and distributing releases. These
modules can be configured many different ways, which can make it difficult to learn
the specific incantations required for each project you are familiar with.

This project uses `invoke <http://www.pyinvoke.org>`_ to provide a clean, high level
interface for these development tasks. To see the full list of functions available::

   $ invoke -l

You can run multiple tasks in a single invocation, for example::

   $ invoke clean docs build

That one command will remove all superflous cache, testing, and build files, render
the documentation, and build a source distribution and a wheel distribution.

To make it easy to check everything before you commit, you can just type::

   $ invoke check
   ...
   $ echo $?
   0

and it will test, lint, and check the format of all the code and the documentation. If
this doesn't complete everything successfully then you still need to fix some stuff
before you commit or submit a pull request. In this context, complete everything
successfully means: all tests pass, lint returns a perfect score, doc8 finds no
errors, etc.

To see what is actually getting executed by ``invoke``, check the ``tasks.py`` file.


Testing
-------

Unit testing provides reliability and consistency in released software. This project
has 100% unit test coverage. Pull requests which reduce test coverage will not
be merged.

This repository has Github Actions configured to run tests when you push or merge a
pull request. Any push triggers a test run against all supported versions of python in
a linux environment. Any pull request triggers a test run against all supported
versions of python on all supported operating systems.

You can run the tests against all the supported versions of python using tox::

   $ tox

tox expects that when it runs ``python3.9`` it will actually get a python from the
3.9.x series. That's why we set up the various python environments earlier.

If you just want to run the tests in your current python environment, use pytest::

   $ pytest

This runs all the test in ``tests/`` and also runs doctests in ``tomcatmanager/`` and
``docs/``.

You can speed up the test suite by using ``pytest-xdist`` to parallelize the tests
across the number of cores you have::

   $ pip install pytest-xdist
   $ pytest -n8


To ensure the tests can run without an external dependencies, this project includes a
mock server for each supported version of Tomcat. This speeds up testing considerably
and also allows you to parallelize tests using ``python-xdist``.

By default, ``pytest`` runs the mock server corresponding to the latest supported
version of Tomcat. If you want to test against a different mock server, do something
like::

   $ pytest --mocktomcat 9.0

Look in ``conftest.py`` to see how these servers are implemented and launched.

When you run the tests with ``tox``, the test suite runs against each supported
version of Tomcat using each supported version of Python.

In many of the doctests you'll see something like::

   >>> tomcat = getfixture("tomcat")

This ``getfixture()`` helper imports fixtures defined in ``conftest.py``, which has
several benefits:

- reduces the amount of redundant code in doctests which shows connecting
  to a tomcat server and handling exceptions
- allows doctests to execute against a mock tomcat server


Testing Against A Real Server
-----------------------------

If you wish, you can run the test suite against a real Tomcat Server instead of
against the mock server included in this distribution. Running the test suite will
deploy and undeploy an app hundreds of times, and will definitely trigger garbage
collection, so you might not want to run it against a production server.

It's also slow (which is why the tests normally run against a mock server). When I run
the test suite against a stock Tomcat on a Linode with 2 cores and 4GB of memory it
takes approximately 3 minutes to complete. I don't think throwing more CPU at this
would make it any faster: during the run of the test suite the Tomcat Server never
consumes more than a few percent of the CPU capacity.

You must prepare some files on the server in order for the test suite to run
successfully. Some of the tests instruct the Tomcat Server to deploy an application
from a warfile stored on the server. I suggest you use the minimal application
included in this distribution at ``tomcatmanager/tests/war/sample.war``, but you can
use any valid war file. Put this file in some directory on the server; I typically put
it in ``/tmp/sample.war``.

You must also construct a minimal context file on the server. You can see an example
of such a context file in ``tomcatmanager/tests/war/context.xml``:

.. code-block:: xml

   <?xml version="1.0" encoding="UTF-8"?>
   <!-- Context configuration file for my web application -->
   <Context path='/ignored' docBase='/tmp/sample.war'>
   </Context>

The ``docBase`` attribute must point to a valid war file or the tests will fail. It
can be the same minimal war file you already put on the server. The ``path`` attribute
is ignored for context files that are not visible to Tomcat when it starts up, so it
doesn't matter what you have there. I typically put this context file at
``/tmp/context.xml``.

You will also need:

- the url where the manager app of your Tomcat Server is available
- a user with the ``manager-script`` role
- the password for the aforementioned user

With all these prerequisites ready, you can feed them to ``pytest`` as shown::

   $ pytest --url=http://localhost:8080/manager --user=ace \
   --password=newenglandclamchowder --warfile=/tmp/sample.war \
   --contextfile=/tmp/context.xml

If your tomcat server uses SSL/TLS client certificates for authentication, you
can specify those certificates instead of a user and password::

   $ pytest --url=https://localhost:8088/manager --cert=/path/to/cert.file \
   --key=/path/to/key.file --warfile=/tmp/sample.war --contextfile=/tmp/context.xml

If your certificate and key are in the same file, pass that file using the ``--cert``
command line option.

.. warning::

   The private key to your local certificate must be unencrypted. The `Requests
   <https://requests.readthedocs.io/en/latest/>`_ library used for network
   communication does not support using encrypted keys.

.. warning::

   If you test against a real Tomcat server, you should not use the ``pytest-xdist``
   plugin to parallelize testing across multiple CPUs or many platforms. Many of the
   tests depend on deploying and undeploying an app at a specific path, and that path
   is shared across the entire test suite. It wouldn't help much anyway because the
   testing is constrained by the speed of the Tomcat server.

If you kill the test suite in the middle of a run, you may leave the test application
deployed in your tomcat server. If this happens, you must undeploy it before rerunning
the test suite or you will get lots of errors.

When the test suite deploys applications, it will be at the path returned by the
``safe_path`` fixture in ``conftest.py``. You can modify that fixture if for some
reason you need to deploy at a different path.


Code Quality
------------

Use ``pylint`` to check code quality. The default pylint config file ``pylintrc``
can be used for both the tests and package::

   $ pylint src tests

You are welcome to use the pylint comment directives to disable certain messages in
the code, but pull requests containing these directives will be carefully scrutinized.


Code Formatting
---------------

Use `ruff <https://docs.astral.sh/ruff/>`_ to format your code.
We use the default configuration, including a line length of 88 characters.

To format all the code in the project using ``ruff``, do::

   $ ruff format *.py tests src docs

You can check whether ``ruff`` would make any formatting changes to the source code by::

   $ ruff format --check *.py tests src docs

Ruff integrates with many common editors and IDE's, that's the easiest way to ensure
that your code is always formatted.

Please format the code in your PR using ``ruff`` before submitting it, this project
is configured to not allow merges if ``ruff format`` would change anything.


Punctuation and Capitalization for Users
----------------------------------------

Messages generated by ``InteractiveTomcatManager`` are intended for consumption
by users, rather than developers.

Usage messages for individual commands are in all lower case letters with no periods.
If the help for a particular option contains multiple phrases, separate them with
a semi-colon. This matches the style of ``argparse.ArgumentParser``. For example the
message generated for the ``-h`` option is an uncapitalized phrase with no period.
``ArgumentParser`` epilogs should be sentences with capitalized first letters.

Error messages are in all lower case letters with no periods. This matches the style
of the errors generated by ``argparse.ArgumentParser``.

Command descriptions as shown by the ``help`` command come from the docstring for
the associated method. For example the description shown for the ``deploy`` command
comes from the the docstring for ``do_deploy``. The code assumes these docstrings
are a single line. These command descriptions are all lower case letters with no
periods. ``ArgumentParser`` objects should get the first line of the docstring to
use for the description, so that ``connect -h`` always shows the same description
as ``help``.

Documentation in ``/docs`` is written in sentences with capitalized first letters.


Punctuation and Capitalization for Developers
---------------------------------------------

Docstrings in ``TomcatManager`` and other associated classes are written in
sentences with capitalized first letters. This matches the style that Sphinx
uses to render the documentation and ensures that all html documentation
(user and api) follows the same style.


Documentation
-------------

Documentation is not an afterthought for this project. All PR's must include relevant
documentation or they will be rejected.

The documentation is written in reStructured Test, and is assembled from both the
``docs/`` directory and from the docstrings in the code. We use `Sphinx formatted
docstrings <https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html>`_.
We encourage references to other methods and classes in docstrings, and choose to
optimize docstrings for clarity and usefulness in the rendered output rather than ease
of reading in the source code.

The documentation is indented using four spaces, the same as the python code.

The code includes type hints as a convenience, but does not provide stub files nor do
we use mypy to check for proper static typing. Our philosophy is that the dynamic
nature of Python is a benefit and we shouldn't impose static type checking, but
annotations of expected types can be helpful for documentation purposes.

`Sphinx <http://www.sphinx-doc.org>`_ transforms the documentation source files
into html::

   $ cd docs
   $ make html

The output will be in ``docs/build/html``. We treat warnings as errors, and the
documentation has none. Pull requests which generate errors when the documentation is
build will be rejected.

If you are doing a lot of documentation work, the `sphinx-autobuild
<https://github.com/GaretJax/sphinx-autobuild>`_ module has been integrated.
Type::

   $ cd docs
   $ make livehtml

Then point your browser at `<http://localhost:8000>`_ to see the
documentation automatically rebuilt as you save your changes.

Use ``doc8`` to check documentation quality::

   $ doc8 docs README.rst CONTRIBUTING.rst CHANGELOG.rst

This project is configured to prevent merges to the main or develop branch if
``doc8`` returns any errors.

When code is pushed to the **main** branch, which only happens when we cut a
new release, the documentation is automatically built and deployed to
`https://tomcatmanager.readthedocs.io/en/stable/
<https://tomcatmanager.readthedocs.io/en/stable/>`_. When code is pushed to the
**develop** branch, the documentation is automatically built and deployed to
`https://tomcatmanager.readthedocs.io/en/develop/
<https://tomcatmanager.readthedocs.io/en/develop/>`_.


Make a Release
--------------

To make a release and deploy it to `PyPI <https://pypi.python.org/pypi>`_, do the
following:

1. Merge everything to be included in the release into the **develop** branch.

2. Run ``tox`` to make sure the tests pass in all the supported python versions.

3. Review and update ``CHANGELOG.rst``.

4. Update and close the milestone corresponding to the release at
   `https://github.com/tomcatmanager/tomcatmanager/milestones
   <https://github.com/tomcatmanager/tomcatmanager/milestones>`_

5. Push the **develop** branch to github.

6. Create a pull request on github to merge the **develop** branch into
   **main**. Wait for the checks to pass.

7. Tag the **develop** branch with the new version number, and push the tag.

8. Merge the **develop** branch into the **main** branch and close the pull
   request.

9. Create a new release on Github.

10. Build source distribution, wheel distribution, and upload them to testpypi::

       $ invoke testpypi

11. Build source distribution, wheel distribution, and upload them to pypi::

       $ invoke pypi

12. Docs are automatically deployed to http://tomcatmanager.readthedocs.io/en/stable/.
    Make sure they look good. Add a "Version" in readthedocs which points to the tag
    you just created. Prune old versions as necessary.

13. Switch back to the **develop** branch.

14. Add an **Unreleased** section to the top of ``CHANGELOG.rst``. Push the
    change to github.
