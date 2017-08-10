## Developing

### Install in place

To have setup.py deploy links to your source code:

	$ python3 setup.py develop

To remove the development links:

	$ python3 setup.py develop --uninstall

### Testing

Install testing dependencies:

	$ pip3 install -e .[test]

Run tests:

	$ pytest
