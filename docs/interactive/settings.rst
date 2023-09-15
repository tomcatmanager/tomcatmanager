Settings
========

View All Settings
-----------------

The ``settings`` command displays a list of settings which control the behavior
of ``tomcat-manager``:

.. code-block:: text

  tomcat-manager> settings
  debug = false                        # show stack trace for exceptions
  echo = false                         # for piped input, echo command to output
  editor = "/opt/homebrew/bin/emacs"   # program used to edit files
  feedback_prefix = "--"               # string to prepend to all feedback output
  prompt = "tm> "                      # the prompt displayed before accepting user input
  quiet = false                        # suppress all feedback and status output
  status_spinner = "bouncingBar"       # style of status spinner from rich.spinner
  status_suffix = "..."                # suffix to append to status messages
  status_to_stdout = false             # status information to stdout instead of stderr
  syntax_theme = "monokai"             # pygments syntax highlighing theme
  theme = "dark"                       # color scheme
  timeout = 10.0                       # seconds to wait for HTTP connections
  timing = false                       # report execution time upon command completion


Change a Setting
----------------

You can change any of these settings using the ``set`` command:

.. code-block:: text

  tomcat-manager> set prompt = "tm> "
  tm> set timeout = 3

* describe TOML syntax for settings


debug
-----

describe the debug setting


echo
----

describe the echo setting

editor
------

describe the editor setting

feedback_prefix
---------------

describe the feedback_prefix setting

prompt
------


quiet
-----


status_spinner
--------------


status_suffix
-------------


status_to_stdout
----------------


syntax_theme
------------


theme
-----



timeout
-------

The number of seconds to wait for a HTTP response from the Tomcat server before timing
out with an error. Set to ``0`` to never timeout (not recommended). Fractions of
seconds are allowed.


timing
------

