Contributing
============

Get Source Code
---------------

Clone the repo from github::

		$ git clone git@github.com:tomcatmanager/tomcatmanager.git


Create python environments
--------------------------

tomcatamanger uses `tox <https://tox.readthedocs.io/en/latest/>`_ to run
the test suite against multiple python versions. I recommend using `pyenv
<https://github.com/pyenv/pyenv>`_ with the `pyenv-virtualenv
<https://github.com/pyenv/pyenv-virtualenv>`_ plugin to manage these
various versions.

This project uses tox for testing, and you will need several versions of
python, with a virtualenv for each one::

    $ cd tomcatmanager
    $ pyenv install 3.6.2
    $ pyenv virtualenv -p python3.6 3.6.2 tomcatmanager-3.6
    $ pyenv install 3.5.3
    $ pyenv virtualenv -p python3.5 3.5.3 tomcatmanager-3.5
    $ pyenv install 3.4.6
    $ pyenv virtualenv -p python3.4 3.4.6 tomcatmanager-3.4

Now set pyenv to make all three of those available at the same time::

    $ pyenv local tomcatmanager-3.6 tomcatmanager-3.5 tomcatmanager-3.4

You now have isolated virtualenvs just for tomcatmanager for each of the
three python versions. This table shows commands on the left, and which
virtualenv it will utilize.

=======    ======  ================
Command    python  virtualenv
=======    ======  =================
python     3.6.2   tomcatmanager-3.6
python3    3.6.2   tomcatmanager-3.6
python3.6  3.6.2   tomcatmanager-3.6
python3.5  3.5.3   tomcatmanager-3.5
python3.4  3.4.6   tomcatmanager-3.4

Same pattern for ``pip`` and other stuff installed with python.


Install dependencies
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


Branches, tags, and versions
----------------------------

This project uses a simplified version of the `git flow branching
strategy <http://nvie.com/posts/a-successful-git-branching-model/>`_. We
don't use release branches, and we generally don't do hotfixes, so we
don't have any of those branches either. The master branch always
contains the latest release of the code uploaded to PyPI, with a tag for
the version number of that release.

The develop branch is where all the action occurs. Feature branches are
welcome. When it's time for a release, we merge develop into master.

This project uses `semantic versioning <http://semver.org/>`_.


Testing
-------

To ensure the tests can run without an external dependencies,
``tests/mock_server80.py`` contains a HTTP server which emulates
the behavior of Tomcat Manager 8.0. There is a test fixture to start
this server, and all the tests run against this fixture.

You can run the tests in all three versions of python using tox::

    $ tox

If you just want to run the tests in your current python environment, use pytest::

	$ pytest

This runs all the test in ``tests/`` and also runs doctests in
``tomcatmanager/`` and ``docs/``.

In many of the doctests you'll see something like:

>>> tomcat = getfixture('tomcat')

This ``getfixture()`` helper imports fixtures defined in ``conftest.py``,
which has several benefits:

- reduces the amount of redundant code in doctests which shows connecting
  to a tomcat server and handling exceptions
- allows doctests to execute against a mock tomcat server

You can run all the tests against a real Tomcat Server that you have running
by utilizing the following command line options::

   $ pytest --url=http://localhost:8080/manager --user=ace \
   --password=newenglandclamchowder --serverwar=/tmp/sample.war

Running the test suite will deploy and undeploy an app dozens of times, and
will definitely trigger garbage collection, so you might not want to run it
against a production server. When an app is deployed, it will be at the path
returned by the ``safe_path`` fixture in ``conftest.py``. You can modify that
fixture if for some reason you need to deploy at a different path.

The ``url``, ``user``, and ``password`` options describe the location anc
credentials for the Tomcat server you wish to use. The ``serverwar`` parameter
is the full path to a war file on the server. There is a simple war file in
``tests/war/sample.war`` which you can copy to the server. If you don't copy
the war file, or if you don't specify the ``serverwar`` parameter, or the path
you provide doesn't point to a valid war file, several of the tests will fail.

.. note::

   If you test against a real Tomcat Server, you should not use the
   ``pytest-xdist`` plugin to parallelize testing across multiple CPUs or many
   platforms. Many of the tests depend on deploying and undeploying an app at a
   specific path, and that path is shared across the entire test suite. It
   wouldn't help much anyway because the testing would be constrained by the
   speed of the Tomcat Server.


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

Then point your browser at `<http://localhost:8000>`_ to see the documentation
automatically rebuilt as you save your changes.


Make a Release
--------------

To make a release and deploy it to `PyPI
<https://pypi.python.org/pypi>`_, do the following:

1. Merge everything to be included in the release into the develop branch.

2. Test

3. Review and update CHANGELOG.rst

4. Merge the develop branch into the master branch.

5. Tag the master branch with the version number

6. Clean the build::

    $ python setup.py clean --dist --eggs --pycache
    $ (cd docs && make clean)
   
7. Build the source distribution::

    $ python3 setup.py sdist

8. Build the wheel::

    $ python3 setup.py bdist_wheel

9. Build the docs::

    $ (cd docs && make html)

10. Deploy the docs?

11. Upload packages to PyPI::

    $ twine upload dist/*
