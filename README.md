# tomcat-manager

If you use Apache Tomcat for any sort of development work you’ve probably deployed lots of applications to it. There are a bunch of ways to get your war files there:

  - use the [Tomcat Manager](https://tomcat.apache.org/tomcat-8.5-doc/manager-howto.html) application in your browser
  - use the [Tomcat Ant Tasks](https://wiki.apache.org/tomcat/AntDeploy) included with Tomcat
  - use [Cargo](https://codehaus-cargo.github.io/) and its plugins for ant and maven

Here's another way. I've created a python script that can do it from the command line by talking to Tomcat Manager application.


## Download and Install

Requires python 3.0 or newer.  If you need python 2.x support, try the python2.x branch.

On macOS, *nix, or *BSD, put the script in `~/bin` and rename it to `tomcat-manager`.

If you use Windows, rename it to `tomcat-manager.py` and put it in your path somewhere. See [http://docs.python.org/3.3/using/windows.html](http://docs.python.org/3.3/using/windows.html) for more details.

## Tomcat Configuration

Users wishing to utilize the Tomcat Manager application must authenticate with the manager application, and also must be assigned at least one of the following roles:

 - manager-gui
 - manager-script
 - manager-jmx
 - manager-status

To use the `tomcat-manager` script, you need a user in `tomcat-users.xml` with access to the `manager-script` role:

	<tomcat-users>
	.....
		<role rolename="manager-script"/>
		<user username="admin" password="newenglandclamchowder" roles="manager-script"/>
	</tomcat-users>

## Connecting to tomcat

When you use the web based manager application included with the tomcat distribution, you typically access it via the url `http://localhost:8080/manager/html`. This script requires a similar http connection, but the URL is different.

If you can access the web based tomcat manager application at `http://localhost:8080/manager/html`, then you should use `http://localhost:8080/manager` for this script.

## Usage

This script can either be used in command line mode or interactive mode. To
use interactive mode you can do:

    $ tomcat-manager
	tomcat-manager> connect http://localhost:8080/manager admin newenglandclamchowder
	tomcat-manager> list
	Path                     Status  Sessions Directory
	------------------------ ------- -------- ------------------------------------
	/                        running        0 ROOT
	/manager                 running       14 /usr/share/tomcat7-admin/manager
	/host-manager            running        0 /usr/share/tomcat7-admin/host-manager
	tomcat-manager> exit

Command line mode might look like:

	$ tomcat-manager --user=admin http://localhost:8080/manager list
	Password: {you type your password here}
	Path                     Status  Sessions Directory
	------------------------ ------- -------- ------------------------------------
	/                        running        0 ROOT
	/manager                 running       17 /usr/share/tomcat7-admin/manager
	/host-manager            running        0 /usr/share/tomcat7-admin/host-manager

To see all of the valid commands, use interactive mode:

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



For help on a particular command:

	$ tomcat-manager
	tomcat-manager> help connect
	usage: connect url [username] [password]
	tomcat-manager>


## Tomcat Features

The following functions from the [Tomcat Manager](https://tomcat.apache.org/tomcat-8.5-doc/manager-howto.html) web application are available:

 - **list** - show all applications running inside the tomcat server
 - **deploy** - install a local war file in the tomcat server
 - **undeploy** - stop execution of and remove a tomcat application from the tomcat server
 - **start** - start a tomcat application that has already been deployed in the tomcat server
 - **stop** - stop execution of a tomcat application but leave it deployed in the tomcat server
 - **reload** - stop and start a tomcat application
 - **sessions** - display active sessions for a particular tomcat application, with a breakdown of session inactivity by time
 - **expire** - expire idle sessions
 - **serverinfo** - give some information about the tomcat server, including JVM version, OS Architecture and version, and Tomcat version
 - **status** - get XML document with details of tomcat server
 - **resources** - show the JNDI resources configured in tomcat
 - **findleaks** - find tomcat apps that are leaking memory
 - **sslconnectorciphers** - show SSL/TLS ciphers configured for each connector
 - **threaddump** - show a jvm thread dump
 - **vminfo** - show information about the jvm


There are a few commands that don't do anything to Tomcat, but are necessary for or enhance the operation of the script:

 - **connect** - link to an instance of the tomcat manager by url, user and password
 - **exit_code** - show the value of the exit_code variable, similar to $? in sh/ksh/bash
 - **version** show the version information about this script
 - **help** - get help about a particular command, including usage and parameters
 - **exit** - if you are in interactive mode, exit back to the command line
 - **quit** - same as exit

## Interactive Mode Features

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

	>>> print(self.tomcat_manager.serverinfo())
	{'Tomcat Version': 'Apache Tomcat/8.0.32 (Ubuntu)', 'OS Name': 'Linux', 'OS Version': '4.4.0-89-generic', 'OS Architecture': 'amd64', 'JVM Version': '1.8.0_131-8u131-b11-2ubuntu1.16.04.3-b11', 'JVM Vendor': 'Oracle Corporation'}


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
