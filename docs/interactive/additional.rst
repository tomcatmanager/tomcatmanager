Additional Features
===================

Readline Editing
----------------

You can edit current or previous commands using standard ``readline`` editing
keys. If you aren't familiar with ``readline``, just know that you can use your
arrow keys, ``home`` to move to the beginning of the line, ``end`` to move to
the end of the line, and ``delete`` to forward delete characters.


Command History
---------------

Interactive mode keeps a command history, which you can navigate using the up
and down arrow keys. and search the history of your commands with
``<control>+r``.

You can view the list of previously issued commands:

.. code-block:: text

    tomcat-manager> history

And run a previous command by string search:

.. code-block:: text

    tomcat-manager> history -r undeploy

Or by number:

.. code-block:: text

    tomcat-manager> history -r 10

The ``history`` command has many other options, including the ability to save
commands to a file and load commands from a file. Use ``help history`` to get
the details.


Shell-style Output Redirection
------------------------------

Save the output of the ``list`` command to a file:

.. code-block:: text

    tomcat-manager> list > /tmp/tomcat-apps.txt

Search the output of the ``vminfo`` command:

.. code-block:: text

    tomcat-manager> vminfo | grep user.timezone
      user.timezone: US/Mountain

Or the particularly useful:

.. code-block:: text

    tomcat-manager> threaddump | less


Clipboard Integration
---------------------

You can copy output to the clipboard by redirecting but not giving a filename:

.. code-block:: text

    tomcat-manager> list >

You can also append output to the clipboard using a similar method:

.. code-block:: text

    tomcat-manager> serverinfo >>


Run shell commands
------------------

Use the ``shell`` or ``!`` commands to execute operating system commands (how
meta):

.. code-block:: text

    tomcat-manager> !ls

Of course tab completion works on shell commands.


Python Interpreter
------------------------------------

You can launch a python interpreter:

.. code-block:: text

    tomcat-manager> py
    Python 3.10.0 (default, Oct  7 2021, 15:03:23) [Clang 11.0.3 (clang-1103.0.32.62)] on darwin
    Type "help", "copyright", "credits" or "license" for more information.

    Use `Ctrl-D` (Unix) / `Ctrl-Z` (Windows), `quit()`, `exit()` to exit.
    Run CLI commands with: app("command ...")

    >>> self.tomcat
    <tomcatmanager.tomcat_manager.TomcatManager object at 0x10f652a40>
    >>> self.tomcat.is_connected
    True
    >>> exit()
    Now exiting Python shell...

As you can see, if you have connected to a Tomcat server, then you will have a
``self.tomcat`` object available which is an instance of :class:`.TomcatManager`.
See :doc:`/package` for more information about what you can do with this object.
