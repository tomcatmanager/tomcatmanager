Using TomcatManager from Python
===============================

Connect to the server
---------------------

Before you can do anything useful, you need to create a TomcatManager object
and connect it to the server. 

.. automethod:: tomcatmanager.TomcatManager.__init__

Alternatively, you can use the :meth:`TomcatManager.connect` method, which unlike creating the object, actually tries to connect.

.. automethod:: tomcatmanager.TomcatManager.connect


Deploying applications
----------------------
