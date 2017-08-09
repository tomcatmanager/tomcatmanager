#
# Copyright (c) 2007 Jared Crapo
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

"""
tomcatmanager.models
~~~~~~~~~~~~~~~

This module contains the data objects created by and used by tomcatmanager.
"""

from requests.structures import LookupDict


class TomcatError(Exception):
	pass


class TomcatManagerResponse:
	"""The response for a Tomcat Manager command"""    

	def __init__(self, response=None):
		self._response = response
		self._status_code = None
		self._status_message = None
		self._result = None

	@property
	def response(self):
		"""contains the requsts.Response object from the request"""
		return self._response

	@response.setter
	def response(self, response):
		self._response = response
		# parse the text to get the status code and results
		if response.text:
			try:
				statusline = response.text.splitlines()[0]
				self.status_code = statusline.split(' ', 1)[0]
				self.status_message = statusline.split(' ',1)[1][2:]
				self.result = response.text.splitlines()[1:]
			except IndexError:
				pass

	@property
	def status_code(self):
		"""status of the tomcat manager command
		
		the codes can be found in tomcatmanager.codes and they are
		
		tomcatmanager.codes.ok
		tomcatmanager.codes.fail
		"""
		return self._status_code

	@status_code.setter
	def status_code(self, value):
		self._status_code = value

	@property
	def status_message(self):
		return self._status_message
	
	@status_message.setter
	def status_message(self, value):
		self._status_message = value

	@property
	def result(self):
		return self._result

	@result.setter
	def result(self, value):
		self._result = value

	def raise_for_status(self):
		"""raise exceptions if status is not ok
		
		first calls requests.Response.raise_for_status() which will
		raise exceptions if a 4xx or 5xx response is received from the server
		
		If that doesn't raise anything, then check if we have an "FAIL" response
		from the first line of text back from the Tomcat Manager web app, and
		raise an TomcatError if necessary
		
		stole idea from requests package
		"""
		self.response.raise_for_status()
		if self.status_code == codes.fail:
			raise TomcatError(self.status_message)


###
#
# build status codes
#
###
_codes = {

	# 'sent from tomcat': 'friendly name'
	'OK': 'ok',
	'FAIL': 'fail',
}

codes = LookupDict(name='status_codes')

for code, title in _codes.items():
	setattr(codes, title, code)
