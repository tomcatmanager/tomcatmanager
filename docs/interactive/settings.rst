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
    prompt = "tm> "                      # displays before accepting user input
    quiet = false                        # suppress all feedback and status output
    status_prefix = "--"                 # string to prepend to all feedback output
    status_animation = "bouncingBar"     # style of activity spinner from rich.spinner
    status_suffix = "..."                # suffix to append to status messages
    status_to_stdout = false             # status information to stdout instead of stderr
    theme = "default-dark"               # color scheme
    timeout = 10.0                       # seconds to wait for HTTP connections
    timing = false                       # report execution time upon command completion


Change a Setting
----------------

You can change any of these settings using the ``set`` command:

.. code-block:: text

    tomcat-manager> set prompt = "tm> "
    tm> set timeout = 3

You can also change settings using the :doc:`configfile`.

The syntax of the ``set`` command is simple. The first argument is the name of the
setting. You can see all by typing ``settings``, or by scrolling down.

The second argument is an equals sign, ie ``=``.

The third argument is the value of the setting. For settings that are on or off, use
either ``true`` or ``false``. For settings that are a number, like ``timeout``, just
type the number. For settings that are a string, like ``prompt``, enclose the value in
quote marks.

Here's a detailed description of each available setting.


debug
-----

The default value is ``false``. If set to ``true`` a Python stack trace will be
displayed when an exception occurs.


echo
----

The default value is ``false``. If you are piping input into ``tomcat-manager`` from
the shell, it may be useful to have those commands injected into the output, so you
can see the command and the output together. Set to ``true`` to echo piped input
commands into the output.

This setting has no effect if the input is not piped from the operating system shell.
If you turn this on, and are interactively typing commands into ``tomcat-manager``,
they will not be displayed in the output.


editor
------

The ``editor`` setting contains the full path to the program that ``tomcat-manager``
should invoke to edit text files. This setting is used by several commands, most
notable is the ``config edit`` command used to edit the configuration file. If this
setting does not have a value, the contents of the ``EDITOR`` environment variable
will be used.


prompt
------

When used interactively, the ``tomcat-manager`` program displays a prompt before
accepting user input. This setting contains the text to be displayed as the prompt.
You can set this to be an empty string to disable the prompt, but that would be
very confusing.

The default value is ``tomcat-manager>``.


quiet
-----

By default, ``tomcat-manager`` provides useful feedback and status information as it
executes commands. If you don't want to see this information, set ``quiet`` to ``true``.

For example, when ``quiet`` is set to ``false`` (the default), the ``connect`` command
displays:

.. code-block:: text

    tomcat-manager> connect http://localhost:8080/manager ace newenglandclamchowder
    --connecting... [=== ]
    --connected to http://localhost/manager as ace
    --tomcat version: [Apache Tomcat/10.1.0]
    tomcat-manager>

If you set ``quiet`` to ``true``, no feedback information is displayed

.. code-block:: text

    tomcat-manager> set quiet = true
    tomcat-manager> connect http://localhost:8080/manager ace newenglandclamchowder
    tomcat-manager>


status_prefix
---------------

By default, all status and feedback messages begin with ``--``. You can change or
eliminate the prefix value by setting ``status_prefix``. You might change it to:

.. code-block:: text

    tomcat-manager> set status_prefix = ">>"

Set ``status_prefix`` to an empty string to display the status messages with no prefix.


status_animation
----------------

Commands which run on the remote Tomcat server can take some time to finish. For
example, if you are deploying a large application, it may take several seconds for
that application to be transmitted to the server and deployed. ``tomcat-manager``
displays an animated activity indicator for these actions. This setting allows you to
choose the style of the animation. There are several dozen options available.
You can view all the animation styles by:

.. code-block:: bash

    $ python -m rich.spinner

Press ``Control-C`` to exit the demo.

To disable the animated progress display:

.. code-block:: text

    tomcat-manager> set status_animation = ""


status_suffix
-------------

By default, all status and feedback messages end with ``...```. You can change or
eliminate the suffix by setting ``status_suffix`` to the value you would like appended
to status and feedback messages.

Set ``status_suffix`` to an empty string to display status messages with no suffix.


status_to_stdout
----------------

By default, status and feedback messages are sent to the standard error file descriptor.
Set ``status_to_stdout`` to ``true`` to send those messages to standard output.


theme
-----

The theme to use to apply colors to output. See :ref:`interactive/themes:Themes` for
more information.


timeout
-------

The number of seconds to wait for a HTTP response from the Tomcat server before timing
out with an error. Set to ``0`` to never timeout (not recommended). Fractions of
seconds are allowed, for example, you could:

.. code-block:: text

    tomcat-manager> set timeout = 3.5

The default value is ``10``.


timing
------

If ``timing`` is set to ``true``, ``tomcat-manager`` will report the number of seconds
it took for each command to execute after the command has completed. The number of
seconds is displayed as feedback, which means if you have ``quiet`` set to ``true``,
you will not see it.
