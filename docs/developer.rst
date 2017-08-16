Developing tomcatmanager
========================

Get Source Code
---------------

Clone the repo from github::

		$ git clone git@github.com:tomcatmanager/tomcatmanager.git

I recommend using ``virtualenvwrapper`` and friends, especially for
development use. tomcatmanager requires python 3, I assume you've
already got that installed. Create a new environment, and then install
development dependencies::

    $ cd tomcatmanager
    $ mkvirtualenv --python=/usr/local/bin/python3 tomcatmanager
    $ setvirtualenvproject ~/.virtualenvs/tomcatmanager .
    $ workon tomcatmanager
    $ pip install -e .
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


Install in place
----------------

If you want to use the code in your repo as the module that everything
else imports, you can have setup.py deploy the package as links to your
source code instead of copying files to your python ``site-packages``
folder::

    $ python3 setup.py develop

To remove the development links::

    $ python3 setup.py develop --uninstall


Testing
-------

To ensure the tests can run without an external dependencies,
``tests/mock_server80.py`` contains a HTTP server which emulates
the behavior of Tomcat Manager 8.0. There is a test fixture to start
this server, and all the tests run against this fixture.

To run the tests::

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

   $ pytest --url=http://localhost:8080/manager --userid=ace \
   --password=newenglandclamchowder --serverwar=/tmp/sample.war

Running the test suite will deploy and undeploy an app dozens of times, and
will definitely trigger garbage collection, so you might not want to run it
against a production server. When an app is deployed, it will be at the path
returned by the ``safe_path`` fixture in ``conftest.py``. You can modify that
fixture if for some reason you need to deploy at a different path.

The ``url``, ``userid``, and ``password``
options are self-explanatory. The ``serverwar`` parameter is the full path
to a war file on the server. There is a simple war file in
``tests/war/sample.war`` which you can copy to the server. If you don't
copy the war file, or if you don't specify the ``serverwar`` parameter, or
the path you provide doesn't point to a valid war file, several of the
tests will fail.


Documentation
-------------

To build the documentation::

   $ cd docs
   $ make html

The output will be in ``build/docs/html``.


Make a Release
--------------

To make a release and deploy it to `PyPI
<https://pypi.python.org/pypi>`_, do the following:

1. Merge everything to be included in the release into the develop branch.

2. Merge the develop branch into the master branch.

3. Tag the master branch with the version number

4. Clean the build::

    $ python setup.py clean --dist --eggs --pycache
    $ (cd docs && make clean)
   
5. Build the source distribution::

    $ python3 setup.py sdist

6. Build the wheel::

    $ python3 setup.py bdist_wheel

7. Build the docs::

    $ (cd docs && make html)

8. Deploy the docs?

9. Upload packages to PyPI::

    $ twine upload dist/*
