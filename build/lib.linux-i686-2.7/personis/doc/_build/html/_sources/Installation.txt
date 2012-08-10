
Installation
============

These installation instructions assume that you are installing Personis on a linux system with Python 2.6 or 2.7
installed. 

The Personis framework makes use of several packages that are not part
of the default Python installation.
The packages are:

pip install cherrypy google-api-python-client pyyaml shove genshi sqlalchemy

Personis is known to work with these versions and copies are included in
the Personis distribution for your convenience. Personis may work with
more recent versions but this has not been tested.

Quick installation instructions:
 
The distribution of personis is a compressed tar file: Personis-rrr.tgz

First untar the distribution (*rrr* is the release number)::

	$ tar zxf Personis-rrr.tgz

This will create a directory Personis-rrr for the code::

	$ cd Personis-rrr
	$ ls
	Apps		Personis	README		install.sh

To install Personis, use the command::

	$ ./install.sh

The Personis modules are in the Personis/Src directory and can be run directly
from that directory or any other directory by setting your PYTHONPATH
environment variable.
Necessary support packages will be installed in the Personis/lib/python
directory and so that directory must also be in the PYTHONPATH.

The following commands will set the path (where *rrr* is the release number)::

	cd Personis-rrr
	export PYTHONPATH=`pwd`/Personis/Src:`pwd`/Personis/lib/python

You might want to note the value of PYTHONPATH and add a line to 
your .bashrc to set it for future use.
	
