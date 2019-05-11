Contributing
============

Get Source Code
---------------

Clone the repo from github::

	$ git clone git@github.com:tomcatmanager/tomcatmanager.git


Create Python Environments
--------------------------

tomcatamanger uses `tox <https://tox.readthedocs.io/en/latest/>`_ to run
the test suite against multiple python versions. I recommend using `pyenv
<https://github.com/pyenv/pyenv>`_ with the `pyenv-virtualenv
<https://github.com/pyenv/pyenv-virtualenv>`_ plugin to manage these
various versions. If you are a Windows user, `pyenv` won't work for you,
you'll probably have to use `conda <https://conda.io/>`_.

This distribution includes a shell script ``build-pyenvs.sh`` which
automates the creation of these environments.

If you prefer to create these virtual envs by hand, do the following::

    $ cd tomcatmanager
    $ pyenv install 3.7.3
    $ pyenv virtualenv -p python3.7 3.7.3 tomcatmanager-3.7
    $ pyenv install 3.6.8
    $ pyenv virtualenv -p python3.6 3.6.8 tomcatmanager-3.6
    $ pyenv install 3.5.7
    $ pyenv virtualenv -p python3.5 3.5.7 tomcatmanager-3.5
    $ pyenv install 3.4.10
    $ pyenv virtualenv -p python3.4 3.4.10 tomcatmanager-3.4

Now set pyenv to make all three of those available at the same time::

    $ pyenv local tomcatmanager-3.7 tomcatmanager-3.6 tomcatmanager-3.5 tomcatmanager-3.4

Whether you ran the script, or did it by hand, you now have isolated virtualenvs
for each of the minor python versions. This table shows various python commands,
the version of python which will be executed, and the virtualenv it will
utilize.

=============  ======  =================
Command        python   virtualenv
=============  ======  =================
``python``     3.7.3   tomcatmanager-3.7
``python3``    3.7.3   tomcatmanager-3.7
``python3.7``  3.7.3   tomcatmanager-3.7
``python3.6``  3.6.8   tomcatmanager-3.6
``python3.5``  3.5.7   tomcatmanager-3.5
``python3.4``  3.4.10  tomcatmanager-3.4
``pip``        3.7.3   tomcatmanager-3.7
``pip3``       3.7.3   tomcatmanager-3.7
``pip3.7``     3.7.3   tomcatmanager-3.7
``pip3.6``     3.6.8   tomcatmanager-3.6
``pip3.5``     3.5.7   tomcatmanager-3.5
``pip3.4``     3.4.10  tomcatmanager-3.4
=============  ======  =================


Install Dependencies
--------------------

Now install all the development dependencies::

    $ pip install -e .[dev]

This installs the tomcatmanager package "in-place", so the package points
to the source code instead of copying files to the python
``site-packages`` folder.

All the dependencies now have been installed in the ``tomcatmanager-3.6``
virtualenv. If you want to work in other virtualenvs, you'll need to manually
select it, and install again::

   $ pyenv shell tomcatmanager-3.4
   $ pip install -e .[dev]


Branches, Tags, and Versions
----------------------------

This project uses a simplified version of the `git flow branching
strategy <http://nvie.com/posts/a-successful-git-branching-model/>`_. We
don't use release branches, and we generally don't do hotfixes, so we
don't have any of those branches either. The master branch always
contains the latest release of the code uploaded to PyPI, with a tag for
the version number of that release.

The develop branch is where all the action occurs. Feature branches are
welcome. When it's time for a release, we merge develop into master.

This project uses `semantic versioning <https://semver.org/>`_.


Invoking Common Development Tasks
---------------------------------

This project uses many other python modules for various development tasks,
including testing, rendering documentation, and building and distributing
releases. These modules can be configured many different ways, which can
make it difficult to learn the specific incantations required for each
project you are familiar with.

This project uses `invoke <http://www.pyinvoke.org>`_ to provide a clean,
high level interface for these development tasks. To see the full list of
functions available::

   $ invoke -l

You can run multiple tasks in a single invocation, for example::

   $ invoke clean docs sdist wheel

That one command will remove all superflous cache, testing, and build
files, render the documentation, and build a source distribution and a
wheel distribution.

You probably won't need to read further in this document unless you
want more information about the specific tools used.


Testing
-------

To ensure the tests can run without an external dependencies,
``tests/mock_server80.py`` contains a HTTP server which emulates the behavior
of Tomcat Manager 8.0. There is a test fixture to start this server, and all
the tests run against this fixture. I created this fixture to speed up testing
time. It doesn't do everything a real Tomcat server does, but it's close enough for the tests to run, and it allows you to parallelize the test suite using ``python-xdist``.

You can run the tests against all the supported versions of python using tox::

    $ tox

tox expects that when it runs ``python3.4`` it will actually get a python from
the 3.4.x series. That's why we set up the various python environments earlier.

If you just want to run the tests in your current python environment, use
pytest::

	$ pytest

This runs all the test in ``tests/`` and also runs doctests in
``tomcatmanager/`` and ``docs/``.

You can speed up the test suite by using ``pytest-xdist`` to parallelize the
tests across the number of cores you have::

    $ pip install pytest-xdist
    $ pytest -n8

In many of the doctests you'll see something like:

>>> tomcat = getfixture('tomcat')

This ``getfixture()`` helper imports fixtures defined in ``conftest.py``,
which has several benefits:

- reduces the amount of redundant code in doctests which shows connecting
  to a tomcat server and handling exceptions
- allows doctests to execute against a mock tomcat server

You can run all the tests against a real Tomcat Server by utilizing the
following command line options::

   $ pytest --url=http://localhost:8080/manager --user=ace \
   --password=newenglandclamchowder --warfile=/tmp/sample.war \
   --contextfile=/tmp/context.xml

Running the test suite will deploy and undeploy an app hundreds of times, and
will definitely trigger garbage collection, so you might not want to run it
against a production server. When I run the test suite against a stock Tomcat
on a Linode with 2 cores and 4GB of memory it takes approximately 30 minutes
to complete.

.. note::

   If you test against a real Tomcat server, you should not use the
   ``pytest-xdist`` plugin to parallelize testing across multiple CPUs or
   many platforms. Many of the tests depend on deploying and undeploying an
   app at a specific path, and that path is shared across the entire test
   suite. It wouldn't help much anyway because the testing is constrained
   by the speed of the Tomcat server.

If you kill the test suite in the middle of a run, you may leave the test
application deployed in your tomcat server. If this happens, you must undeploy
it before rerunning the test suite or you will get lots of errors.

When the test suite deploys applications, it will be at the path returned by
the ``safe_path`` fixture in ``conftest.py``. You can modify that fixture if
for some reason you need to deploy at a different path.

The ``url``, ``user``, and ``password`` options describe the location and
credentials for the Tomcat server you wish to use.

The ``warfile`` parameter is the full path to a war file on the server. There
is a simple war file in ``tests/war/sample.war`` which you can copy to the
server if you don't have a war file you want to use. If you don't copy the war
file, or if you don't specify the ``warfile`` parameter, or the path you
provide doesn't point to a valid war file, several of the tests will fail.

The ``contextfile`` parameter is the full path to a context XML file, which
gives you an alternative way to specify additional deployment information to
the Tomcat Server. There is a simple context file in ``tests/war/context.xml``
which you can copy to the server if you don't have a context file you want to
use. If you don't copy the context file, or if you don't specify the
``contextfile`` parameter, or the path you provide doesn't point to a valid
context file, several of the tests will fail. The path in your context file
will be ignored, but you must specify a docBase attribute which points to a
real war file.


Code Quality
------------

Use ``pylint`` to check code quality. There is a pylint config file for the
tests and for the main module::

   $ pylint --rcfile=tests/pylintrc tests
   $ pylint --rcfile=tomcatmanager/pylintrc tomcatmanager

You are welcome to use the pylint comment directives to disable certain
messages in the code, but pull requests containing these directives will be
carefully scrutinized.

As allowed by
`PEP 8 <https://www.python.org/dev/peps/pep-0008/#maximum-line-length>`_
this project uses a nominal line length of 100 characters.


Documentation
-------------

The documentation is written in reStructured Test, and turned into HTML using
`Sphinx <http://www.sphinx-doc.org>`_::

   $ cd docs
   $ make html

The output will be in ``docs/build/html``.

If you are doing a lot of documentation work, the `sphinx-autobuild
<https://github.com/GaretJax/sphinx-autobuild>`_ module has been integrated.
Type::

   $ cd docs
   $ make livehtml

Then point your browser at `<http://localhost:8000>`_ to see the
documentation automatically rebuilt as you save your changes.


Make a Release
--------------

To make a release and deploy it to `PyPI
<https://pypi.python.org/pypi>`_, do the following:

1. Merge everything to be included in the release into the **develop** branch.

2. Run ``tox`` to make sure the tests pass in all the supported python versions.

3. Review and update ``CHANGELOG.rst``.

4. Update the milestone corresponding to the release at `https://github.com/tomcatmanager/tomcatmanager/milestones <https://github.com/tomcatmanager/tomcatmanager/milestones>`_

5. Push the **develop** branch to github.

6. Create a pull request on github to merge the **develop** branch into
   **master**. Wait for the checks to pass.

7. Merge the **develop** branch into the **master** branch and close the pull
   request.

8. Tag the **master** branch with the new version number, and push the tag.

9. Build source distribution, wheel distribution, and upload them to pypi staging::

    $ invoke pypi-test

10. Build source distribution, wheel distribution, and upload them to pypi::

    $ invoke pypi

11. Docs are automatically deployed to http://tomcatmanager.readthedocs.io/en/stable/.
   Make sure they look good.

12. Switch back to the **develop** branch. Add an **Unreleased** section to
    the top of ``CHANGELOG.rst``. Push the change to github.
