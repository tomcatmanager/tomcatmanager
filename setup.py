#
# -*- coding: utf-8 -*-
"""setuptools based setup for tomcatmanager

"""

from os import path

from setuptools import setup, find_packages

try:
    from setupext import janitor
    clean_command = janitor.CleanCommand
except ImportError:
    clean_command = None

cmd_classes = {}
if clean_command:
    cmd_classes['clean'] = clean_command

#
# get the long description from the README file
here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='tomcatmanager',
    use_scm_version=True,

    description='A command line tool and python library for managing a tomcat server.',
    long_description=long_description,

    author='Jared Crapo',
    author_email='jared@kotfu.net',
    url='https://github.com/tomcatmanager/tomcatmanager',
    license='MIT',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    keywords='java tomcat command line',

    packages=find_packages(),

    python_requires='>=3.4',
    install_requires=['cmd2>=0.8.0', 'requests', 'appdirs', 'attrdict'],

    setup_requires=['setuptools_scm', 'setupext_janitor'],
    cmdclass=cmd_classes,

    # dependencies for development and testing
    # $ pip3 install -e .[dev]
    extras_require={
        'dev': ['pytest', 'pytest-mock', 'tox', 'codecov', 'pytest-cov',
                'setuptools_scm', 'setupext_janitor',
                'sphinx', 'sphinx-autobuild', 'wheel', 'twine']
    },

    # define the scripts that should be created on installation
    entry_points={
        'console_scripts': [
            'tomcat-manager=tomcatmanager.__main__:main',
        ],
    },

)
