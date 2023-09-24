tomcat-manager
==============

Launching
---------

After installation, you will have a new tool available called
``tomcat-manager``. Run it with no command line arguments to invoke an
interactive, line-oriented command interpreter:

.. code-block:: text

  $ tomcat-manager
  tomcat-manager> connect http://localhost:8080/manager ace newenglandclamchowder
  --connecting... [==  ]
  --connected to http://localhost:8080/manager as ace
  --tomcat version: [Apache Tomcat/10.1.0]
  tomcat-manager> list
  --listing applications... [==  ]
  --Listed applications for virtual host [localhost]
  Path                     Status  Sessions Directory
  ------------------------ ------- -------- ------------------------------------
  /                        running        0 ROOT
  /manager                 running       14 /usr/share/tomcat7-admin/manager
  /host-manager            running        0 /usr/share/tomcat7-admin/host-manager
  tomcat-manager> exit

Use the ``exit`` or ``quit`` command to exit the interpreter and return to your
operating system shell.

.. code-block:: text

  $ tomcat-manager [url] list


Available Commands
------------------

The interactive shell has a built-in list of all available commands:

.. code-block:: text

  tomcat-manager> help
  tomcat-manager is a command line tool for managing a Tomcat server

  Type 'help [command]' for help on any command.

  Here's a categorized list of all available commands:

  Connecting to a Tomcat server
  ────────────────────────────────────────────────────────────────────────
  connect      connect to a tomcat manager instance
  which        show the url of the tomcat server you are connected to
  disconnect   disconnect from a tomcat manager instance

  Managing applications
  ────────────────────────────────────────────────────────────────────────
  list       show all installed tomcat applications
  deploy     deploy an application to the tomcat server
  redeploy   deploy an application to the tomcat server after undeploying the given path
  undeploy   remove an application from the tomcat server
  start      start a deployed tomcat application that isn't running
  stop       stop a tomcat application and leave it deployed on the server
  restart    stop and start a tomcat application
    reload   synonym for 'restart'
  sessions   show active sessions for a tomcat application
  expire     expire idle sessions

  Server information
  ────────────────────────────────────────────────────────────────────────
  findleakers   show tomcat applications that leak memory
  resources     show global JNDI resources configured in tomcat
  serverinfo    show information about the tomcat server
  status        show server status information in xml format
  threaddump    show a jvm thread dump
  vminfo        show diagnostic information about the jvm

  TLS configuration
  ────────────────────────────────────────────────────────────────────────
  sslconnectorciphers        show SSL/TLS ciphers configured for each connector
  sslconnectorcerts          show SSL/TLS certificate chain for each connector
  sslconnectortrustedcerts   show SSL/TLS trusted certificates for each connector
  sslreload                  reload SSL/TLS certificates and keys

  Settings, configuration, and tools
  ────────────────────────────────────────────────────────────────────────
  config         edit or show the location of the user configuration file
  edit           edit a file in the preferred text editor
  exit_code      show a number indicating the status of the previous command
  history        view, run, edit, and save previously entered commands
  py             run an interactive python shell
  run_pyscript   run a file containing a python script
  settings       display program settings
  set            change a program setting
  shell          execute a command in the operating system shell
  shortcuts      show shortcuts for other commands

  Other
  ────────────────────────────────────────────────────────────────────────
  exit      exit the interactive command prompt
    quit    synonym for the 'exit' command
  help      show available commands, or help on a specific command
  version   show the version number of this program
  license   show the software license for this program



As well as help for each command:

.. code-block:: text

   tomcat-manager> help stop
   usage: stop [-h] [-v VERSION] path

   Stop a running tomcat application and leave it deployed on the server.

   positional arguments:
     path                  The path part of the URL where the application is
                           deployed.

   optional arguments:
     -h, --help            show this help message and exit
     -v VERSION, --version VERSION
                           Optional version string of the application to stop. If
                           the application was deployed with a version string, it
                           must be specified in order to stop the application.

This document does not include detailed explanations of every command. It does
show how to connect to a Tomcat server and deploy a war file, since there are
quite a few options for both of those commands. For everything else, the
built-in help should be sufficient.
