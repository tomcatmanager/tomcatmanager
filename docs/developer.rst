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


Make a Release
--------------

To make a release and deploy it to `PyPI
<https://pypi.python.org/pypi>`_, do the following:

1. Merge everything to be included in the release into the develop branch.

2. Ensure ``setup.py`` and ``docs/source/conf.py`` have the correct version number. If not, commit the proper version number to the develop branch.

3. Merge the develop branch into the master branch.

4. Tag the master branch with the version number

5. Clean the build::

    $ python3 setup.py clean --all
    $ rm -rf dist/

6. Build the source distribution::

    $ python3 setup.py sdist

7. Build the wheel::

    $ python3 setup.py bdist_wheel

8. Build the docs::

    $ python3 setup.py build_docs

9. Deploy the docs?

10. Upload packages to PyPI::

    $ twine upload dist/*

11. Checkout the develop branch and update the version numbers in ``setup.py`` and ``docs/source/conf.py``.
