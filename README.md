tomcat-manager
--------------

If you use Apache Tomcat for any sort of development work you’ve probably deployed lots of applications to it. There are a bunch of ways to get your war files there, you can use the manager application in your browser, or you can use Cargo and its plugins for ant and maven. Here's a python script that can do it from the command line.

Download and Install
--------------------

On OS X, *nix, or *BSD, put the script in `~/bin` and rename it to `tomcat-manager`.

If you use Windows, rename it to `tomcat-manager.py` and put it in your path somewhere.  See http://docs.python.org/3.3/using/windows.html for more details.

Usage
-----

This script can either be used in command line mode or interactive mode. To use interactive mode you can do:

    $ tomcat-manager
	tomcat-manager> connect http://localhost:8080/manager admin newenglandclamchowder
	tomcat-manager> list
	Path                           Status  Sessions
	------------------------------ ------- --------
	/manager                       running 114     
	/                              running 0       
	/host-manager                  running 0
	tomcat-manager> exit

Command line mode might look like:

	$ tomcat-manager --user=admin --password=newenglandclamchowder http://localhost:8080/manager list
	Path                           Status  Sessions
	------------------------------ ------- --------
	/manager                       running 117     
	/                              running 0       
	/host-manager                  running 0

To see all of the valid commands, use interactive mode, like this:

	$ tomcat-manager
	tomcat-manager> help

	Documented commands (type help {command}):
	========================================
	EOF      deploy  help  quit    serverinfo  start  undeploy
	connect  exit    list  reload  sessions    stop 

	Miscellaneous help topics:
	==========================
	license  commandline

	tomcat-manager> exit

License
-------
Check the LICENSE file, but it's the MIT License, which means you can do whatever you want, as long as you keep the copyright notice.
