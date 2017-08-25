#
# -*- coding: utf-8 -*-
"""setuptools based setup for tomcatmanager

"""

from setuptools import setup, find_packages
from codecs import open
from os import path

try:
   from setupext import janitor
   CleanCommand = janitor.CleanCommand
except ImportError:
   CleanCommand = None

cmd_classes = {}
if CleanCommand is not None:
   cmd_classes['clean'] = CleanCommand

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
	install_requires=['cmd2', 'requests', 'appdirs'],
	
    setup_requires=['setuptools_scm', 'setupext_janitor'],
    cmdclass=cmd_classes,
    
	# dependencies for development and testing
	# $ pip3 install -e .[dev]
	extras_require={
		'dev': ['pytest', 'tox', 'codecov', 'sphinx', 'sphinx-autobuild',
                'wheel', 'setuptools_scm', 'setupext_janitor', 'twine']
	},

	# define the scripts that should be created on installation
	entry_points={
		'console_scripts': [
			'tomcat-manager=tomcatmanager.__main__:main',
		],
	},

)
