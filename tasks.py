#
# -*- coding: utf-8 -*-

import shutil

import invoke

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

@invoke.task
def pytest(c):
    "Run unit and integrations tests using pytest"
    c.run("pytest")
namespace.add_task(pytest)

@invoke.task
def pytest_clean(c):
    "Remove pytest cache directories"
    dirs = ['.pytest-cache', '.cache']
    rmrf(dirs)
namespace_clean.add_task(pytest_clean, 'pytest')
