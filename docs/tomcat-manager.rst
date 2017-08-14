tomcat-manager command line tool
================================

This script can either be used in command line mode or interactive mode. To
use interactive mode you can do::

   $ tomcat-manager
   tomcat-manager> connect http://localhost:8080/manager admin newenglandclamchowder
   tomcat-manager> list
   Path                     Status  Sessions Directory
   ------------------------ ------- -------- ------------------------------------
   /                        running        0 ROOT
   /manager                 running       14 /usr/share/tomcat7-admin/manager
   /host-manager            running        0 /usr/share/tomcat7-admin/host-manager
   tomcat-manager> exit

Command line mode might look like::

   $ tomcat-manager --user=admin http://localhost:8080/manager list
   Password: {you type your password here}
   Path                     Status  Sessions Directory
   ------------------------ ------- -------- ------------------------------------
   /                        running        0 ROOT
   /manager                 running       17 /usr/share/tomcat7-admin/manager
   /host-manager            running        0 /usr/share/tomcat7-admin/host-manager

To see all of the valid commands, use interactive mode::

   $ tomcat-manager
   tomcat-manager> help


   Documented commands (type help <topic>):
   ========================================
   EOF      exit_code  license  resources            start       undeploy
   connect  expire     list     serverinfo           status      version
   deploy   findleaks  quit     sessions             stop        vminfo
   exit     help       reload   sslconnectorciphers  threaddump

   Miscellaneous help topics:
   ==========================
   commandline


For help on a particular command::

	$ tomcat-manager
	tomcat-manager> help connect
	usage: connect url [username] [password]
	tomcat-manager>

Interactive Mode Features
-------------------------

Interactive mode has a rich set of capabilities, mostly provided by the readline library. It keeps a command history, which you can navigate using the up and down arrow keys. You can edit current or previous commands using standard editing keys, and search the history of your commands with `<control>+r`.

Exit interactive mode using the `quit` or `exit` command.

## Options

By default we use the [cmd](https://docs.python.org/3/library/cmd.html) module from the standard python library. If you want more advanced functionality, you can install the [cmd2](https://cmd2.readthedocs.io/en/latest/index.html) package. This script will notice it's there, and will use it, enabling all the nifty tricks described in this section. All of these examples assume that you are at the interactive prompt and have already successfully connected to the Tomcat Manager web app.

### Improved history

Show history of all commands

	tomcat-manager> history

Type `help history` for more options

Run a previous command by string search

	tomcat-manager> run rel

Type `help run` for more options

### Shell-style output redirection

Save the output of the `list` command to a file

	tomcat-manager> list > /tmp/tomcat-apps.txt

Search the output of the `vminfo` command

	tomcat-manager> vminfo | grep user.timezone
	  user.timezone: America/Denver

### Clipboard integration

Copy or append output to clipboard by redirecting but not giving a filename

	tomcat-manager> list >

### Save and load command history

Save and load command history. Type `help save`, `help load` for details. `load` allows you to script commands in a text file and then run them interactively, for example:

	tomcat-manager> load mycommands.txt

### Edit commands using the editor of your choice

Use EDITOR environment variable to edit the last command, and then execute it

	tomcat-manager> edit

### Run shell commands

	tomcat-manager> ! ls

Tab completion even works on shell commands and files

### Launch in-process python interpreter

	tomcat-manager> py

This launches a python interpreter, with our own objects available. From that python interpreter, you can access the TomcatManager class via like so:

	tomcat-manager> py
	Python 3.6.1 (default, Apr  4 2017, 09:40:51)
	[GCC 4.2.1 Compatible Apple LLVM 8.0.0 (clang-800.0.42.1)] on darwin
	Type "help", "copyright", "credits" or "license" for more information.
	(InteractiveTomcatManager)

			py <command>: Executes a Python command.
			py: Enters interactive Python mode.
			End with ``Ctrl-D`` (Unix) / ``Ctrl-Z`` (Windows), ``quit()``, '`exit()``.
			Non-python commands can be issued with ``cmd("your command")``.
			Run python code from external script files with ``run("script.py")``
