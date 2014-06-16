GNS3-ias
========

GNS3 image access server.

Linux/Unix
----------

Dependencies:

- Python version 3.3 or above
- pip & setuptools must be installed, please see http://pip.readthedocs.org/en/latest/installing.html
  (or sudo apt-get install python3-pip but install more packages)
- virtualenv was used during development
- virtualenv -p /usr/bin/python3.4 --distribute env (Remember to activate your virtualenv if used )
- sudo apt-get install libcurl4-gnutls-dev
- python-dateutil, to install pip install python-dateutil
- pycurl, to install pip install pycurl

.. code:: bash

   cd gns3-ias
   virtualenv -p /usr/bin/python3.4 --distribute env
   source ./env/bin/activate
   python setup.py install
   cd gns3ias
   gns3ias or gns3ias --help

