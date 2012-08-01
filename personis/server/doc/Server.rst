
Personis Server
===============

Personis operates as a library that is imported by application programs and stores models in the local file
system.

Personis can also be run as a server, providing an interface to models for remote clients. In this case the API is almost the same, the only difference being the modules that is imported and used for the Access call, and the
specification of the model to be accessed.

In the case of locally stored models, access requires a *modeldir* argument to specify the 
location of the stored models, as well as the name of the model (a simple ID). 
For models accessed remotely via the server, *modeldir* is not used and the model name has the form:
name@server[:port].

For example, to access the model for "alice" stored on the server "models.server.com" we 
would use the statements::

	import Personis

	um = Personis.Access(model="alice@models.server.com", user='myapp', password='pass')

Running a Server
----------------

It is very easy to run your own Personis server to provide access to models for remote clients.

A server gets configuration information from the file $HOME/.personis_server.conf.
This file specifies the port that the server is to use as well as some miscellaneous configuration options.
A suitable personis_server.conf file can be found in the Personis/Src directory. This can be copied into 
$HOME/.personis_server.conf and the port number changed as desired.

A server can be started for any set of models stored in the same directory using the command::

	# assuming that PYTHONPATH, MODELDIR and LOGFILE are initialised
	Personis.py  --models $MODELDIR --log $LOGFILE &

The directory containing the models is specified in $MODELDIR.
Log information is written to $LOGFILE. This includes information on all requests, error messages etc.


