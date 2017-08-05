# tomcat-manager

If you use Apache Tomcat for any sort of development work you’ve probably deployed lots of applications to it. There are a bunch of ways to get your war files there:

  - use the [Tomcat Manager](https://tomcat.apache.org/tomcat-8.5-doc/manager-howto.html) application in your browser
  - use the [Tomcat Ant Tasks](https://wiki.apache.org/tomcat/AntDeploy) included with Tomcat
  - use [Cargo](https://codehaus-cargo.github.io/) and its plugins for ant and maven

Here's another way. I've created a python script that can do it from the command line by talking to Tomcat Manager application.


# Download and Install

Requires python 3.0 or newer.  If you need python 2.x support, try the python2.x branch.

On macOS, *nix, or *BSD, put the script in `~/bin` and rename it to `tomcat-manager`.

If you use Windows, rename it to `tomcat-manager.py` and put it in your path somewhere. See [http://docs.python.org/3.3/using/windows.html](http://docs.python.org/3.3/using/windows.html) for more details.

# Tomcat Configuration

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

# Connecting to tomcat

When you use the web based manager application included with the tomcat distribution, you typically access it via the url `http://localhost:8080/manager/html`. This script requires a similar http connection, but the URL is different.

If you can access the web based tomcat manager application at `http://localhost:8080/manager/html`, then you should use `http://localhost:8080/manager` for this script.

# Usage

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

	$ tomcat-manager --user=admin --password=newenglandclamchowder http://localhost:8080/manager list
	Path                     Status  Sessions Directory
	------------------------ ------- -------- ------------------------------------
	/                        running        0 ROOT
	/manager                 running       17 /usr/share/tomcat7-admin/manager
	/host-manager            running        0 /usr/share/tomcat7-admin/host-manager

To see all of the valid commands, use interactive mode:

	$ tomcat-manager
	tomcat-manager> help

	Documented commands (type help {command}):
	========================================
	EOF      deploy  help  quit    serverinfo  start  undeploy
	connect  exit    list  reload  sessions    stop 

	Miscellaneous help topics:
	==========================
	license  commandline

For help on a particular command:

	$ tomcat-manager
	tomcat-manager> help connect
	usage: connect url [username] [password]
	tomcat-manager>


# Features

This script can perform all of the same functions that can be done with the web based tomcat-admin application included with tomcat. The following functions are available:

 -   ****serverinfo**** - give some information about the tomcat server, including JVM version, OS Architecture and version, and Tomcat version
 -   **sessions** - display active sessions for a particular tomcat application, with a breakdown of session inactivity by time
 -   **list** - show all applications running inside the tomcat server
 -   **deploy** - install a local war file in the tomcat server
 -   **undeploy** - stop execution of and remove a tomcat application from the tomcat server
 -   **start** - start a tomcat application that has already been deployed in the tomcat server
 -   **stop** - stop execution of a tomcat application but leave it deployed in the tomcat server
 -   **reload** - stop and start a tomcat application
 -   **resources** - show the JNDI resources configured in tomcat


There are a few commands that don't do anything to Tomcat, but are necessary for utilization of the script:

 -   **connect** - link to an instance of the tomcat manager by url, user and password
 -   **help** - get help about a particular command, including usage and parameters
 -   **exit** - if you are in interactive mode, exit back to the command line

# License

Check the LICENSE file. It's the MIT License, which means you can do whatever
you want, as long as you keep the copyright notice.
