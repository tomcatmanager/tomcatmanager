#
# -*- coding: utf-8 -*-

import os
import shutil

import invoke

#
# TODO
# - move docs/build to build/docs?

# shared function
def rmrf(dirs):
    if isinstance(dirs, str):
        dirs = [dirs]
    
    for dir_ in dirs:
        print("Removing {}".format(dir_))
        # shutil.rmtree(dir_, ignore_errors=True)


# create namespaces
namespace = invoke.Collection() 
namespace_clean = invoke.Collection('clean')
namespace.add_collection(namespace_clean, 'clean')
namespace_docs = invoke.Collection('docs')
namespace.add_collection(namespace_docs, 'docs')

#####
#
# testing with pytest and tox
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
namespace_docs.add_task(docs_build, 'build')

@invoke.task
def docs_clean(c):
    "Remove rendered documentation"
    rmrf(DOCS_BUILDDIR)
namespace_clean.add_task(docs_clean, 'docs')

@invoke.task
def docs_livehtml(c):
    "Launch webserver on http://localhost:8000 with rendered documentation"
    watch = '-z tomcatmanager -z tests'
    builder = 'html'
    outputdir = os.path.join(DOCS_BUILDDIR, builder)
    cmdline = 'sphinx-autobuild -b {} {} {} {}'.format(builder, DOCS_SRCDIR, outputdir, watch)
    c.run(cmdline, pty=True)
namespace_docs.add_task(docs_livehtml, 'livehtml')

#
# make a dummy clean task which runs all the tasks in the clean namespace
clean_tasks = list(namespace_clean.tasks.values())
@invoke.task(pre=list(namespace_clean.tasks.values()), default=True)
def clean_all(c):
    pass
namespace_clean.add_task(clean_all, 'all')