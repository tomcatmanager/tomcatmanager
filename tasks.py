#
# -*- coding: utf-8 -*-

import os
import shutil

import invoke

#
# TODO
# - move docs/build to build/docs?

# shared function
def rmrf(dirs, verbose=True):
    if isinstance(dirs, str):
        dirs = [dirs]
    
    for dir_ in dirs:
        if verbose:
            print("Removing {}".format(dir_))
        # shutil.rmtree(dir_, ignore_errors=True)


# create namespaces
namespace = invoke.Collection() 
namespace_clean = invoke.Collection('clean')
namespace.add_collection(namespace_clean, 'clean')

#####
#
# pytest, tox, and codecov
#
#####
@invoke.task
def pytest(c):
    "Run unit and integration tests using pytest"
    c.run("pytest")
namespace.add_task(pytest)

@invoke.task
def pytest_clean(c):
    "Remove pytest cache directories"
    dirs = ['.pytest-cache', '.cache']
    rmrf(dirs)
namespace_clean.add_task(pytest_clean, 'pytest')

@invoke.task
def tox(c):
    "Run unit and integration tests on multiple python versions using tox"
    c.run("tox")
namespace.add_task(tox)

@invoke.task
def tox_clean(c):
    "Remove tox virtualenvs and logs"
    rmrf('.tox')
namespace_clean.add_task(tox_clean, 'tox')

@invoke.task
def codecov_clean(c):
    "Remove code coverage reports"
    dirs = set()
    for name in os.listdir(os.curdir):
        if name.startswith('.coverage'):
            dirs.add(name)
    rmrf(dirs)
namespace_clean.add_task(codecov_clean, 'coverage')


#####
#
# documentation
#
#####
DOCS_SRCDIR='docs'
DOCS_BUILDDIR=os.path.join('docs','build')

@invoke.task(default=True)
def docs_build(c, builder='html'):
    "Build documentation using sphinx"
    cmdline = 'python -msphinx -M {} {} {}'.format(builder, DOCS_SRCDIR, DOCS_BUILDDIR)
    c.run(cmdline)
namespace.add_task(docs_build, name='docs')

@invoke.task
def docs_clean(c):
    "Remove rendered documentation"
    rmrf(DOCS_BUILDDIR)
namespace_clean.add_task(docs_clean, name='docs')

@invoke.task
def docs_livehtml(c):
    "Launch webserver on http://localhost:8000 with rendered documentation"
    watch = '-z tomcatmanager -z tests'
    builder = 'html'
    outputdir = os.path.join(DOCS_BUILDDIR, builder)
    cmdline = 'sphinx-autobuild -b {} {} {} {}'.format(builder, DOCS_SRCDIR, outputdir, watch)
    c.run(cmdline, pty=True)
namespace.add_task(docs_livehtml, name='livehtml')

#####
#
# build and distribute
#
#####
BUILDDIR='build'
DISTDIR='dist'


@invoke.task
def build_clean(c):
    "Remove the build directory"
    rmrf(BUILDDIR)
namespace_clean.add_task(build_clean, 'build')

@invoke.task
def dist_clean(c):
    "Remove the dist directory"
    rmrf(DISTDIR)
namespace_clean.add_task(dist_clean, 'dist')

@invoke.task
def eggs_clean(c):
    "Remove egg directories"
    dirs = set()
    dirs.add('.eggs')
    for name in os.listdir(os.curdir):
        if name.endswith('.egg-info'):
            dirs.add(name)
        if name.endswith('.egg'):
            dirs.add(name)
    rmrf(dirs)
namespace_clean.add_task(eggs_clean, 'eggs')

@invoke.task
def pycache_clean(c):
    "Remove __pycache__ directories"
    dirs = set()
    for root, dirnames, _ in os.walk(os.curdir):
        if '__pycache__' in dirnames:
            dirs.add(os.path.join(root, '__pycache__'))
    print("Removing __pycache__ directories")
    rmrf(dirs, verbose=False)
namespace_clean.add_task(pycache_clean, 'pycache')

@invoke.task
def build_sdist(c):
    "Create a source distribution"
    c.run('python setup.py sdist')
namespace.add_task(build_sdist, 'sdist')

@invoke.task
def build_wheel(c):
    "Build a wheel distribution"
    c.run('python setup.py bdist_wheel')
namespace.add_task(build_wheel, 'wheel')

@invoke.task(pre=[dist_clean, build_clean, build_sdist, build_wheel])
def build_distribute(c):
    "Build and upload a distribution to pypi"
    c.run('twine upload dist/*')
namespace.add_task(build_distribute, 'distribute')

#
# make a dummy clean task which runs all the tasks in the clean namespace
clean_tasks = list(namespace_clean.tasks.values())
@invoke.task(pre=list(namespace_clean.tasks.values()), default=True)
def clean_all(c):
    pass
namespace_clean.add_task(clean_all, 'all')