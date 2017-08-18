Command Line
============

You've already read about :doc:`Interactive Use <interactive>` right? If not,
this part will feel kind of hollow.

Say you want to find out how many active sessions there are in the oldest
version of our `shiny` app (told you it would feel kind of hollow). You could
use interactive mode:

.. code-block:: none

   $ tomcat-manager
   tomcat-manager>connect https://www.example.com/manager ace newenglandclamchowder
   tomcat-manager>list
   Path                     Status  Sessions Directory
   ------------------------ ------- -------- ------------------------------------
   /                        running        0 ROOT
   /manager                 running        0 manager
   /shiny                   running       17 shiny##v2.0.6
   /shiny                   running        6 shiny##v2.0.5

But you want to do it from a shell script. So here it is:

.. code-block:: bash

   #!/usr/bin/env bash
   #
   URL=https://www.example.com/manager
   USERID=ace
   PASSWD=newenglandclamchowder
   COMMAND=list
   TOMCAT="tomcat-manager --user=$USERID --password=$PASSWD $URL $COMMAND"
   
   # get the output of the list into a shell variable
   LIST=$($TOMCAT)

   # if the tomcat command completed successfully
   TOMCAT_EXIT=$?
   if [ "$TOMCAT_EXIT" -eq 0 ]; then
       echo "$LIST" | grep '^/shiny' | awk '{ print $4, $3}' | \
       sort | head -1 | cut -d' ' -f2
   else
       # list has an error message, not the list of tomcat apps
       echo -n "$LIST"
       exit $TOMCAT_EXIT
   fi

Save this script as ``~/bin/oldshiners.sh``, and then run it:

.. code-block:: bash

   $ ~/bin/oldshiners.sh
   6

As you can see in the shell script, we build a ``tomcat-manager`` command which
included authentication credentials, the url where the Tomcat Manager web app
is deployed, as well as the command from :doc:`Interactive Use <interactive>`.
You have to specify all of this on the command line. In this example, we used
``list`` as our command. Any command that works in the interactive mode works
on the command line.

Note how we check the exit code in the shell. ``tomcat-manager`` knows whether
the command to the tomcat server completed successfully or not, and sets the
shell exit code appropriately. The shell exit codes are:

   | **0** - command completed succesfully
   | **1** - command had an error
   | **2** - incorrect usage
   | **127** - unknown command


Server Shortcuts
----------------

You an also use :ref:`server_shortcuts` from the command line with or without
commands:

.. code-block:: none

   $ tomcat-manager localhost
   tomcat-manager>list
   Path                     Status  Sessions Directory
   ------------------------ ------- -------- ------------------------------------
   /                        running        0 ROOT
   /manager                 running        0 manager

Or:

.. code-block:: none

   $ tomcat-manager localhost list
   Path                     Status  Sessions Directory
   ------------------------ ------- -------- ------------------------------------
   /                        running        0 ROOT
   /manager                 running        0 manager

