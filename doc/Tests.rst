
Tests
=====

Personis uses the standard python unittest package. The tests are in the /personis/test directory
and can be run using the command:

	$cd test
	$./runtests.sh

which is a simple wrapper of::

	$python -m unittest discover -t ../..

There is some support for running a local server (try testserver.sh) but it's rather deprecated. It's better just to point the test_server.py script at an installed server (by configuring client_secrets.json).