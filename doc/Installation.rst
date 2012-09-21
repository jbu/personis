
Installation
============

These installation instructions assume that you are installing Personis on a linux system with Python 2.7
installed. 

By far the simplest way to install personis is::

	pip install personis

Personis uses a number of other libraries, but the install process should find
and download the correct versions. If you don't wish to change your system python
installation, you can use virtualenv::

	mkdir personis-sandbox
	cd personis-sandbox
	wget https://raw.github.com/pypa/virtualenv/master/virtualenv.py
	python virtualenv.py --distribute .
	./bin/pip install personis

Windows
-------

Some examples (the activity watcher, for example) use win32api. To use this, first install win32api. Then, if you want to use a virtualenv sandbox::

	python virtualenv.py --distribute --system-site-packages .

Source, etc
-----------

If you wish to customise your installation further, we recommend getting the distribution
from http://pypi.python.org/pypi/personis or the source from https://github.com/jbu/personis.

.. _clientconfig:
Client Configuration
--------------------

You will need to know the URI of a personis server to connect to. You can install one yourself as per the following section if you don't have one already available. Once you have one, most clients are configured to connect to a particular server by editing a 'client_secrets.json' file::

	{
	  "installed": {
	    "client_id": "dfadfadfsdfdwrwe",
	    "client_secret":"fadklsfjlk2rj2klrwej",
	    "redirect_uris": ["http://localhost:8080"],
	    "auth_uri": "https://s0.personis.name/authorize",
	    "token_uri": "https://s0.personis.name/request_token"
	  }
	}

The client_id and client_secret are provided by the personis server (see the https://<personis server/list_clients). The auth_uri and token_uri point to the correct URIs at the personis server you will use. In this case our client is a local (command line) application, so our redirect_uri is a local address. If the client is running on a web server, the redirect_uri would be provided by that server to take part in the OAuth2 authentication.

The client may then be run as (for example)::

	jbu@enterprise:~$ python -m personis.examples.browser
	Welcome James
	Personis Model Browser
	[''] > 

Server Configuration
--------------------

The server requires some configuration. Take the files found at https://github.com/jbu/personis/tree/master/server-conf
and save them in the directory from which you will run your server.

Oauth
~~~~~

It currently uses Google for authentication. Yes, users need a google account. This also means that your personis
server must be registered as a Google API Client. See https://code.google.com/apis/console to register your server as a 
new project and create a 'client id for web applications'. This will give you:

 * A client ID
 * A client secret

You will provide

 * A redirect URI (which will be https://<your personis server>/logged_in)
 * Javascript Origins (which will be your personis server URI)

Find the file 'client_secrets_google.json' which will look like::

	{
	  "web": {
	    "client_id": "lafdkfsjogleusercontent.com",
	    "client_secret": "xxxxxxxxxxxxxxxxxxxx",
	    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
	    "token_uri": "https://accounts.google.com/o/oauth2/token",
	    "redirect_uris": ["http://me.com/logged_in"]
	  }
	}

and enter the information from the client console. 

Overview of the Python Oauth library that we use: https://developers.google.com/api-client-library/python/guide/aaa_oauth

Admins
~~~~~~

Find the file 'admins.yaml' which will look like::

'mickeymouse': 'mickey.mouse@example.com'
'minniemouse': 'minnie.mouse@example.com'

And replace the examples with your admin names. The two fields are your google username with periods (.) removed, followed by your gmail address.

Server
~~~~~~

The cherrypy server is configured from 'server.conf'. You must ensure at least socket_host and socket_port are correct, and the paths in the resource sections point to the personis server source directory.

HTTPS
~~~~~

Parts of the Oauth login should (some say MUST) run over https to ensure security. To enable https in cherrypy, install the pyopenssl library, create certificates, and enable them. Because this is a bit of a pain, the default installation does not do this. But you should. A good overview of creating self-signed certificates can be found at http://www.akadia.com/services/ssh_test_certificate.html