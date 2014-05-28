Personis user model server
==========================

The project consists of 4 parts (so far). 
   * server - the user model server
   * client - a command line client for manipulating a user model
   * log-llum - a really simple web server logging app that uses the personis
                server. Use as an example.
   * activity_sensor - a sensor that logs period of user activity
                  to personis.

All are implemented in python. Python2.7.4 has been the development version.

[![Build Status](https://travis-ci.org/jbu/personis.png)](https://travis-ci.org/jbu/personis)

Installation
============

Server: 
  The server is most handily run using the runserver.sh script. Edit this
script to adjust the required paths and to pass in the correct config
files. You can see that there are a few config files:
   python Personis.py --models=../models/ --config=personis_server.conf --oauthconfig=oauth.yaml --admins=admins.yaml
 --models gives the models directory
 --config is the cherrypy server conf
 --oauthconfig is the config for the oauth CLIENT side of personis server
 --admins is the yaml file of people who can admin the server

 Personis server is a client to the google oauth service, and gets user
 information from google. 

If you want to run Personis independently of the original setup (ie, you're
not in our research group) you can create your own google API project at 
https://code.google.com/apis/console#access and set up a new google 
API project to get your own client id and secret for personis. These go
in oauth.yaml
You can find the user id for admins.yaml by looking for the long number
in the url for your google+ profile.

When you run the server, take note of the URI of the server.

Clients:
  Clients require some information to associate with the personis server.
The server also needs each client registered.
  Go to the server /list_clients page (ie the URI + /list_clients) (you need
  to be a server admin)
  Press the + button on the page to add an entry for the client. This will
  give you a client id and secret, but you can change the friendly name, 
  icon url, and you will need to change the callback url to wherever you
  installed the client. (command line clients just need a localhost url)
  
Each client has an oauth.yaml. Copy the client secret and id to the yaml file,
add the personis server url. Make sure the callback entry is correct.

Command line clients are just run (python xxx.py). They start a web browser
to do the authentication stuff - just follow along.

Inner workings of server
========================

The server exposes a number of URLs. Some are for authentication, some for
administration, and the rest as part of the personis protocol. Here are the 
most important ones:

  /authorize is the oauth2 authentication start point for clients logging in
             (well actually the web browser trying to access the client)
             so log-llum or mneme redirect web browsers here.
  /list_clients is for administrators to register clients with personis
  /list_apps is for users to administer which apps have permission to use
             their model
  /xxxx the 'default' method implements urls for the personis protocol, like
        'ask' or 'tell'. Should only be accessed by json clients. not browsers.

Of less importance for most people are:

admin:
  /list_clients_save and /list_apps_save - for editing the client and app lists

other auth bits:
  /login - the auth point for users/admins loging into the /list pages
  /logged_in - the callback from the google oauth servers. Should be called
               when the request has been validated by google.
  /allow - called when the user says that the client should have access
           to their user model
  /dissallow - opposite.
  /request_token - called by the client to exchange their temporary access
                   token for a real one. Usually the client is at this point
                   the web service (like log-llum or mneme), not a web browser.
                   Ideally (in fact MUST) this is only accessed over TLS/SSL.
