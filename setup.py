#
# -*- coding: utf-8 -*-
"""setuptools based setup for tomcatmanager

"""

from os import path

from setuptools import setup, find_packages

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
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],

    keywords='java tomcat command line',

    packages=find_packages(where="src"),
    package_dir={'':'src'},

    python_requires='>=3.5',
    install_requires=[
        'cmd2>=0.9.14', 'requests', 'appdirs', 'attrdict',
        ],

    setup_requires=['setuptools_scm'],

    # dependencies for development and testing
    # $ pip install -e .[dev]
    extras_require={
        'dev': ['pytest', 'pytest-mock', 'tox',
                'codecov', 'pytest-cov', 'pylint',
                'setuptools_scm', 'wheel', 'twine', 'rope', 'invoke',
                'sphinx', 'sphinx-autobuild', 'sphinx_rtd_theme', 'doc8',],
    },

    # define the scripts that should be created on installation
    entry_points={
        'console_scripts': [
            'tomcat-manager=tomcatmanager.__main__:main',
        ],
    },

)
