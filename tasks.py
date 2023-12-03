#
# -*- coding: utf-8 -*-
"""Development related tasks to be run with 'invoke'"""

import os
import pathlib
import shutil

# make it easy on ourselves, the context argument is often unused
# pylint: disable=unused-argument


import invoke


# shared function
def rmrf(items, verbose=True):
    "Silently remove a list of directories or files"
    if isinstance(items, str) or isinstance(items, pathlib.PosixPath):
        items = [items]

    for item in items:
        if verbose:
            print(f"Removing {item}")
        shutil.rmtree(item, ignore_errors=True)
        # rmtree doesn't remove bare files
        try:
            os.remove(item)
        except FileNotFoundError:
            pass


# create namespaces
namespace = invoke.Collection()
namespace_clean = invoke.Collection("clean")
namespace.add_collection(namespace_clean, "clean")

namespace_check = invoke.Collection("check")
namespace.add_collection(namespace_check, "check")


#####
#
# pytest, tox, pylint, and codecov
#
#####
@invoke.task
def pytest(context):
    "Run tests and code coverage using pytest"
    context.run("pytest", echo=True, pty=True)


namespace_check.add_task(pytest)


@invoke.task
def pytest_clean(context):
    "Remove pytest cache and code coverage files and directories"
    dirs = [".pytest_cache", ".cache", ".coverage"]
    rmrf(dirs)


namespace_clean.add_task(pytest_clean, "pytest")


@invoke.task
def tox(context):
    "Run unit and integration tests on multiple python versions using tox"
    context.run("tox", echo=True)


namespace_check.add_task(tox)


@invoke.task
def tox_clean(context):
    "Remove tox virtualenvs and logs"
    rmrf(".tox")


namespace_clean.add_task(tox_clean, "tox")


@invoke.task
def pylint(context):
    "Check code quality using pylint"
    context.run("pylint src/tomcatmanager tests", echo=True)


namespace_check.add_task(pylint)


@invoke.task(name="format")
def format_check(context):
    """Check if code is properly formatted using ruff"""
    context.run("ruff format --check *.py tests src docs", echo=True)


namespace_check.add_task(format_check)


@invoke.task()
def format(context):
    """Format code using ruff"""
    context.run("ruff format *.py tests src docs", echo=True)


namespace.add_task(format)


#####
#
# documentation
#
#####
DOCS_SRCDIR = pathlib.Path("docs")
DOCS_ADDITIONAL = "README.rst CONTRIBUTING.rst CHANGELOG.rst"
DOCS_BUILDDIR = DOCS_SRCDIR / "build"
SPHINX_OPTS = "-nvWT"  # Be nitpicky, verbose, and treat warnings as errors


@invoke.task()
def docs(context, builder="html"):
    "Build documentation using sphinx"
    cmdline = (
        f"python -msphinx -M {builder} {DOCS_SRCDIR} {DOCS_BUILDDIR} {SPHINX_OPTS}"
    )
    context.run(cmdline, echo=True)


namespace.add_task(docs)
namespace_check.add_task(docs)


@invoke.task()
def doc8(context):
    "Check documentation with doc8"
    context.run(f"doc8 {DOCS_SRCDIR} {DOCS_ADDITIONAL}", echo=True)


namespace_check.add_task(doc8)


@invoke.task
def docs_clean(context):
    "Remove rendered documentation"
    rmrf(DOCS_BUILDDIR)


namespace_clean.add_task(docs_clean, name="docs")


@invoke.task
def livehtml(context):
    "Launch webserver on http://localhost:8000 with rendered documentation"
    watch = "--watch src/tomcatmanager --watch tests --watch ."
    builder = "html"
    outputdir = DOCS_BUILDDIR / builder
    cmdline = f"sphinx-autobuild -b {builder} {DOCS_SRCDIR} {outputdir} {watch}"
    context.run(cmdline, echo=True, pty=True)


namespace.add_task(livehtml)


#####
#
# build and distribute
#
#####
DISTDIR = pathlib.Path("dist")


@invoke.task
def dist_clean(context):
    "Remove the dist directory"
    rmrf(DISTDIR)


namespace_clean.add_task(dist_clean, "dist")


@invoke.task
def eggs_clean(context):
    "Remove egg directories"
    dirs = set()
    dirs.add(".eggs")
    for _, _, files in os.walk(os.curdir):
        for file in files:
            if file.endswith(".egg"):
                dirs.add(file)
    rmrf(dirs)


namespace_clean.add_task(eggs_clean, "eggs")


@invoke.task
def bytecode_clean(context):
    "Remove __pycache__ directories and *.pyc files"
    dirs = set()
    for dirpath, _, files in os.walk(os.curdir):
        if dirpath == "__pycache__":
            dirs.add(dirpath)
        for file in files:
            if file.endswith(".pyc"):
                dirs.add(os.path.join(dirpath, file))
    print("Removing __pycache__ directories and .pyc files")
    rmrf(dirs, verbose=False)


namespace_clean.add_task(bytecode_clean, "bytecode")


@invoke.task(pre=list(namespace_clean.tasks.values()), default=True)
def clean_all(context):
    "Clean everything"


namespace_clean.add_task(clean_all, "all")


@invoke.task(pre=[clean_all])
def build(context):
    "Create a source distribution"
    context.run("python -m build")


namespace.add_task(build)


@invoke.task(pre=[build])
def twine(context):
    "Check for rendering errors in README.rst"
    context.run("twine check dist/*")


namespace_check.add_task(twine)


@invoke.task(pre=[build, twine])
def pypi(context):
    "Build and upload a distribution to pypi"
    context.run("twine upload dist/*")


namespace.add_task(pypi)


@invoke.task(pre=[build, twine])
def testpypi(context):
    "Build and upload a distribution to https://test.pypi.org"
    context.run("twine upload -r testpypi dist/*")


namespace.add_task(testpypi)

# we don't need pytest here because tox will run pytest for us
checktasks = []
for task in list(namespace_check.tasks.values()):
    if task.name != "pytest":
        checktasks.append(task)


@invoke.task(pre=checktasks, default=True)
def check_all(context):
    "Run this before you commit or submit a pull request"


namespace_check.add_task(check_all, "all")
