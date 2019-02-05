Installing asyncpraw
===============

asyncpraw supports python 2.7, 3.3, 3.4, 3.5, and 3.6. The recommended way to
install asyncpraw is via ``pip``.

.. code-block:: bash

   pip install asyncpraw

.. note:: Depending on your system, you may need to use ``pip3`` to install
          packages for python 3.

.. warning:: Avoid using ``sudo`` to install packages. Do you `really` trust
             this package?

For instructions on installing python and pip see "The Hitchhiker's Guide to
Python" `Installation Guides
<http://docs.python-guide.org/en/latest/starting/installation/>`_.

Updating asyncpraw
-------------

asyncpraw can be updated by running:

.. code-block:: bash

   pip install --upgrade asyncpraw

Installing Older Versions
-------------------------

Older versions of asyncpraw can be installed by specifying the version number as
part of the installation command:

.. code-block:: bash

   pip install asyncpraw==3.6.0

Installing the Latest Development Version
-----------------------------------------

Is there a feature that was recently merged into asyncpraw that you cannot wait to
take advantage of? If so, you can install asyncpraw directly from github like so:

.. code-block:: bash

   pip install --upgrade https://github.com/asyncpraw-dev/asyncpraw/archive/master.zip
