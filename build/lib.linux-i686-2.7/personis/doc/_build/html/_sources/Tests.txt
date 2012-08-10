
Tests
=====

The test scripts are divided into those that test the base Personis
module for models stored on the local machine (base), and those that
test the server Personis module for models accessed via a network
connection (server). In both cases the driver test script gives you the
option of nominating a directory to store test models. In the base case
the models are accessed directly by the methods in the Personis_base
module. In the server case, a Personis server is started to provide
access to the models.

To run the tests, change into the Personis directory and::

	$ bash Tests/base-tests
	PYTHONPATH is ....../Personis/Src
	model directory? [..../Tests/Models]

at this point the test script is asking for a directory to store the test models. The default directory
is "Models" in the Tests directory. You can accept this default by pressing return, or type another pathname.

You are now given the option of removing any models previously placed in the test directory. This is useful if
you want to rerun the tests from scratch and create the models again. If you press return you will get
the default response of "No", typing "Y" will remove the existing models::

	Remove models in ......./Src/models? [N]

If you say Yes (or when you run it for the first time) the models will be recreated. 
This will produce a lot of output showing all the model parts as they are created.

Next you are given the option of running all the available base tests, running a particular test, or no tests.
The base test scripts are stored in the directory Tests/Base and are numbered. If you are testing a particular 
feature you can type the number, but to start we suggest typing return for all tests.
The tests now run, one a time, waiting for you to press return before starting the next. If you want to stop
you can press Control-C::

	Test number? (CR for all, ctrl-C if none)

	Running tests...

	====================================================================
				  Tests/Base/example01_add.py
	====================================================================
	add evidence to alice's model
	===================================================================
	Now check the evidence list for alice's names
	===================================================================
	Component:  First name
	===================================================================


		...lots more output...


	=================
	All Done.
	=================

There should be only a small number of python error messages and these will have some explanation in the output.

There are a set of similar tests for the server that can be run with the command::

	$ bash Tests/server-tests

		...lots of output...

	=================
	All Done.
	=================


The models are created in a similar way for the server tests but a server process is started and the
client-server protocol used to access them. The server test scripts can be found in Tests/Server.
