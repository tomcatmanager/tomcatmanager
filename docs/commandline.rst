Command Line
============

You've already read about :doc:`interactive use <interactive/tomcatmanager>` right? If
not, this part will feel kind of hollow.

Any interactive command can be run from the command line. The first positional
argument to ``tomcat-manager`` is the url of the server. The rest of the arguments are
any commands and their arguments from :ref:`interactive/tomcatmanager:Available
Commands`. Here's a few examples:

.. code-block:: text

    $ tomcat-manager --user ace --password newenglandclamchowder \
    http://localhost:8080/manager deploy server /tmp/myfancyapp.war /fancy

.. code-block:: text

    $ tomcat-manager --user ace --password newenglandclamchowder \
    http://localhost:8080/manager list --state running --by path



Using Shell Scripts
-------------------

Say you want to find out how many active sessions there are in the oldest version of
our ``shiny`` app (told you it would feel kind of hollow). You could use interactive
mode:

.. code-block:: text

    $ tomcat-manager
    tomcat-manager>connect https://www.example.com/manager ace newenglandclamchowder
    --connected to https://www.example.com/manager as ace
    tomcat-manager>list
    Path                     Status  Sessions Directory
    ------------------------ ------- -------- ------------------------------------
    /                        running        0 ROOT
    /manager                 running        0 manager
    /shiny                   running       17 shiny##v2.0.6
    /shiny                   running        6 shiny##v2.0.5

If you need to automate a more complex sequence of commands or parse the
output, you might choose to use ``tomcat-manager`` from within a shell script:

.. code-block:: bash

    #!/usr/bin/env bash
    #
    URL=https://www.example.com/manager
    USERID=ace
    PASSWD=newenglandclamchowder
    COMMAND="list --raw"
    TOMCAT="tomcat-manager --quiet --user=$USERID --password=$PASSWD $URL $COMMAND"

    # get the output of the list into a shell variable
    LIST=$($TOMCAT)

    # if the tomcat command completed successfully
    TOMCAT_EXIT=$?
    if [ "$TOMCAT_EXIT" -eq 0 ]; then
        echo "$LIST" | grep '^/shiny' | awk -F ':' '{ print $4":"$3}' | \
        sort | head -1 | awk -F ':' '{ print #2 }'
    else
        # list has an error message, not the list of tomcat apps
        echo -n "$LIST"
        exit $TOMCAT_EXIT
    fi

Save this script as ``~/bin/oldshiners.sh``, and then run it:

.. code-block:: text

   $ ~/bin/oldshiners.sh
   6

This script builds a ``tomcat-manager`` command which includes authentication
credentials, the url where the Tomcat Manager web app is deployed, as well as the
command from :ref:`Available Commands <interactive/tomcatmanager:Available Commands>`.
In this example, we used ``list`` as our command. Any command that works in the
interactive mode works on the command line.

Note how we check the exit code in the shell. ``tomcat-manager`` knows whether
the command to the tomcat server completed successfully or not, and sets the
shell exit code appropriately. The exit codes are:

    | **0** = command completed succesfully
    | **1** = command had an error
    | **2** = incorrect usage
    | **127** = unknown command


Timeout
-------

By default, network operations timeout in 10 seconds. You can change this
value in the :doc:`configuration file <interactive/configfile>`. You can
also override it on the command line.

.. code-block:: text

    $ tomcat-manager --timeout=2.5 http://localhost:8080/manager list

This command line option allows you to override the ``timeout`` :ref:`setting
<interactive/settings:timeout>`.


Authentication
--------------

Use the user you created when you :doc:`Configured Tomcat <configuretomcat>` on the
command line:

.. code-block:: text

    $ tomcat-manager --user=ace http://localhost:8080/manager list
    Password:

and you will be prompted for the password. You can also specify the password on
the command line, but this is not secure:

.. code-block:: text

    $ tomcat-manager --user=ace --password=newenglandclamchowder \
    http://localhost:8080/manager list
    Password:

See :doc:`authentication` for complete details of all supported authentication
mechanisms.

If you want unattended authenticated access, server definitions are a better
option.


Server Definitions
------------------

You can use :ref:`interactive/configfile:Server Definitions` from the command line
with or without commands:

.. code-block:: text

    $ tomcat-manager localhost
    --connected to http://localhost:8080/manager as ace
    tomcat-manager>list
    Path                     Status  Sessions Directory
    ------------------------ ------- -------- ------------------------------------
    /                        running        0 ROOT
    /manager                 running        0 manager

Or:

.. code-block:: text

    $ tomcat-manager localhost list
    --connected to http://localhost:8080/manager as ace
    Path                     Status  Sessions Directory
    ------------------------ ------- -------- ------------------------------------
    /                        running        0 ROOT
    /manager                 running        0 manager

This mechanism allows you to keep all authentication credentials out of your
scripts. Simply create server definitions with credentials for the server(s) you want
to manage, and reference the definitions in your scripts. Instead of this:

.. code-block:: bash

    TOMCAT="tomcat-manager --user=$USERID --password=$PASSWD $URL $COMMAND"

you might use this:

.. code-block:: bash

    TOMCAT="tomcat-manager example $COMMAND"

with the following in your configuration file:

.. code-block:: toml

    [example]
    url = "https://www.example.com"
    user = "ace"
    password = "newenglandclamchowder"


Piped Input
-----------

``tomcat-manager`` will process lines from standard input as though they were
entered at the interactive prompt. There is no mechanism to check for errors
this way, the commands are blindly run until the pipe is closed. The shell exit
code of ``tomcat-manager`` will be the exit code of the last command run.

If you want to see what the exit codes are, you can either use ``$?`` in your
shell, or you can use the interactive command ``exit_code`` (``$?`` works too)
to see the result.

If you want more sophisticated error checking, then you should probably write a
shell script and invoke ``tomcat-manager`` seperately for each command you want
to execute. That will allow you to use the shell script for checking exit
codes, logic branching, looping, etc.


Controlling Output
------------------

When using ``tomcat-manager`` from the command line, you have fine grained
control of what you want included in the output. As a well-behaved shell
program it sends output to ``stdout`` and errors to ``stderr``. If you are
using ``bash`` or one of the other ``sh`` variants, you can easily co-mingle
them into a single stream:

.. code-block:: text

    $ tomcat-manager localhost list > myapps.txt 2>&1

In addition to redirecting with the shell, there are several command line switches
that change what's included in the output. These options correspond to :ref:`Setting
<interactive/settings:Settings>` you can change in :doc:`interactive use
<interactive/tomcatmanager>`. All of the settings default to ``False``, but be aware
that you may have altered them your :doc:`configuration file
<interactive/configfile>`, which is read on startup.

==========================  ====================  =====================================
Option                      Setting                 Description
==========================  ====================  =====================================
``-e, --echo``              ``echo``              Add the command to the output stream.
``-q, --quiet``             ``quiet``             Don't show non-essential feedback.
``-s, --status-to-stdout``  ``status_to_stdout``  Send status information to ``stdout``
                                                  instead of ``stderr``.
``-d, --debug``             ``debug``             Show detailed exception and stack
                                                  trace, even if ``quiet`` is True.
==========================  ====================  =====================================

Some commands show additional status information during their execution which
is not part of the output. If ``quiet=True`` then all status output is
suppressed. If ``quiet=False`` then status information is sent to ``stderr``.
If ``status_to_stdout=True`` then status information is sent to ``stdout``, as
long as ``quiet=False``.

Here's a couple of examples to demonstrate, using a :ref:`server definition
<interactive/configfile:Server Definitions>` of ``localhost``, which we assume gets you
authenticated to a Tomcat Server web application:

These two commands yield the same output, but by different mechanisms: the
first one uses the shell to redirect status messages to the bitbucket, the
second one uses the ``--quiet`` switch to instruct ``tomcat-manager`` to
suppress status messages.

.. code-block:: text

    $ tomcat-manager localhost list 2>/dev/null
    Path                     Status  Sessions Directory
    ------------------------ ------- -------- ------------------------------------
    /                        running        0 ROOT
    /manager                 running        0 manager
    $ tomcat-manager --quiet localhost list 2>/dev/null
    Path                     Status  Sessions Directory
    ------------------------ ------- -------- ------------------------------------
    /                        running        0 ROOT
    /manager                 running        0 manager

If you pipe commands into ``tomcat-manager`` instead of providing them as
arguments, the ``--echo`` command line switch can be included which will print
the prompt and command to the output:

.. code-block:: text

    $ echo list | tomcat-manager --echo localhost
    --connected to https://home.kotfu.net/manager as ace
    tomcat-manager> list
    Path                     Status  Sessions Directory
    ------------------------ ------- -------- ------------------------------------
    /                        running        0 ROOT
    /manager                 running        0 manager

For most common errors, like failed authorization, connection timeouts, and DNS
lookup failures, ``tomcat-manager`` catches the exceptions raised by those
errors, and outputs a terse message describing the problem. For example, if my
Tomcat container is not currently running, or if the HTTP request fails for any
other reason, you will see something like this:

.. code-block:: text

    $ tomcat-manager vm list
    connection error

If you want all the gory detail, give the ``--debug`` command line switch or
set ``debug=True``. Then you'll see something like this (stack trace truncated
with '...'):

.. code-block:: text

    $ tm --debug vm list
    Traceback (most recent call last):
        File "/Users/kotfu/.pyenv/versions/3.6.2/envs/tomcatmanager-3.6/lib/python3.6/site-packages/urllib3/connection.py", line 141, in _new_conn
        (self.host, self.port), self.timeout, **extra_kw)
        File "/Users/kotfu/.pyenv/versions/3.6.2/envs/tomcatmanager-3.6/lib/python3.6/site-packages/urllib3/util/connection.py", line 83, in create_connection
        raise err
        File "/Users/kotfu/.pyenv/versions/3.6.2/envs/tomcatmanager-3.6/lib/python3.6/site-packages/urllib3/util/connection.py", line 73, in create_connection
        sock.connect(sa)
    socket.timeout: timed out
    ...
    requests.exceptions.ConnectTimeout: HTTPConnectionPool(host='192.168.13.66', port=8080): Max retries exceeded with url: /manager/text/serverinfo (Caused by ConnectTimeoutError(<urllib3.connection.HTTPConnection object at 0x103180a20>, 'Connection to 192.168.13.66 timed out. (connect timeout=2)'))
