Using TomcatManager from Python
===============================

Connect to the server
---------------------

Before you can do anything useful, you need to create a :class:`TomcatManager` object
and connect it to the server. 

.. automethod:: tomcatmanager.TomcatManager.__init__

Alternatively, you can use the :meth:`TomcatManager.connect` method, which unlike creating the object, actually tries to connect to the server.

.. automethod:: tomcatmanager.TomcatManager.connect


Responses from the server
-------------------------

Methods in the :class:`TomcatManager` class which talk to the server return
a :class:`TomcatManagerResponse` object.

.. autoclass:: tomcatmanager.models.TomcatManagerResponse
   :members:

Deploying applications
----------------------

.. automethod:: tomcatmanager.TomcatManager.deploy


