

Tutorial Introduction to Personis
=================================

This tutorial assumes you have installed the framework using the instructions in the Installation section.
But as a quick recap for installing the client only:

Create a sandbox directory (u:\\comp5047, perhaps). Download https://raw.github.com/pypa/virtualenv/master/virtualenv.py to the directory. Create a python sandbox::

	u:
	cd \comp5047
	c:\python2.6\python.exe virtualenv.py .

Install necessary libraries

	u:\comp5047\Scripts\pip install google-api-python-client pyyaml personis

Install the client examples from https://github.com/downloads/jbu/personis/clients.zip

Using the *umbrowser* command line utility, the tutorial will take you through the construction, navigation and 
management of a user model.

umbrowser
---------

The umbrowser.py program is a commandline utility that allows most
operations of the Personis system to be carried out interactively.

Umbrowser is found in the clients/browser directory of the personis package and is started with
the command ./umbrowser.py (unix)::

	$ ./umbrowser.py

or for windows::

	u:
	cd \comp5047
	\comp5047\Scripts\python.exe umbrowser.py

The first time you run umbrowser it opens a web browser tab and goes through a login sequence. Usually two screens are presented: one at google that asks you to verify your identity, and one at the personis server asking whether you want to allow umbrowser access to your model (the correct answer is 'yes'). If this is the first time accessing your model, one will be created for you. At the end of this you should end up at a prompt::

	[''] >

The prompt indicates that the browser is waiting for a command. The
initial part shows the current context, with the root context as an
empty string.

The help command gives information about the available commands::

	[''] > help
	Documented commands (type help <topic>):
	========================================
	app         delapp        export      login        mkmodel  set       subscribe
	attributes  delcomponent  import      ls           model    setgoals  tell     
	base        delsub        importmdef  mkcomponent  quit     setperm 
	cd          do            listapps    mkcontext    server   showperm

	Undocumented commands:
	======================
	help

Now we can see what is in the model::

	[''] > ls
	Components:
	Contexts: [u'Devices', u'Personal', u'Apps', u'Goals']
	Views: {}
	Subscriptions: {}

The "ls" command is a like the Unix ls command: it lists what is in the
current context.
As you can see, the model is empty - no components, contexts, views or
subscriptions.
So let's make a new context called "Prefs" in the current (root) context::

	[''] > mkcontext Prefs
	Context description? My preferences
	Create new context 'Prefs' in context '['']' with description 'My preferences'
	Ok?[N] Y

	[''] > ls
	Components:
	Contexts: [u'Devices', u'Personal', u'Apps', u'Goals', u'Prefs']
	Views: {}
	Subscriptions: {}

Now we will change context to the new "Prefs" context and make a
component "food" for our food preferences::

	[''] > cd Prefs
	
	['', 'Prefs'] > mkcomponent food
	Component description? type of food I prefer
	Component type:
	0 attribute
	1 activity
	2 knowledge
	3 belief
	4 preference
	5 goal
	Index? 4
	Value type:
	0 string
	1 number
	2 boolean
	3 enum
	4 JSON
	Index? 0
	Creating new component 'food', type 'preference', description 'type of food I prefer', value type 'string'
	Ok?[N] Y
	
	['', 'Prefs'] > ls
	Components:
		food: type of food I prefer
	Contexts: []
	Views: {}
	Subscriptions: {}
	
	['', 'Prefs'] > 

Now we have a model owned by you that has one 
context "Prefs" containing one component "food".
Now, imagine that you like Thai food so we will add some evidence to your food
preference component using the "tell" command::

	['', 'Prefs'] > tell food
	Value? Thai
	Evidence type:
	0 explicit
	1 implicit
	2 exmachina
	3 inferred
	4 stereotype
	Index? [0]
	Evidence flag? (CR for none)
	Tell value=Thai, type=explicit, flags=[], source=alice, context=['', 'Prefs'], component=food 
	Ok?[N] Y

	
	['', 'Prefs'] > ls
	Components:
		food: type of food I prefer
	Contexts: []
	Views: {}
	Subscriptions: {}

We can now examine the "food" component with the "ls" command::

	['', 'Prefs'] > ls food
	===================================================================
	Component:  type of food I prefer
	===================================================================
	showobj:
	[...]
	  value = Thai
	[...]
	---------------------------------
	Evidence about it
	---------------------------------
	showobj:
		[...]
	---------------------------------
	
Try doing the "tell" operation again with a different food preference and then "ls food" to see the additional
evidence that has been accreted.


To quit the model browser, use the *quit* command.

Logger
------

On a web browser (your phone will do) go to http://personislog.appspot.com/. Here you will be able to log some activity like eating some fruit. Click on one of the icons to log an activity. Now, let's see what happened to your model.

Start umbrowser, as in the previous section::

	$ ./umbrowser.py 
	Welcome James
	Personis Model Browser
	[''] > ls
	Components:
	Contexts: [u'Devices', u'Personal', u'Apps', u'Prefs']
	Views: {}
	Subscriptions: {}
	[''] > cd Apps
	['', 'Apps'] > ls
	Components:
	Contexts: [u'Logging']
	Views: {}
	Subscriptions: {}
	['', 'Apps'] > cd Logging
	['', 'Apps', 'Logging'] > ls
	Components:
		logged_items: All the items logged
	Contexts: []
	Views: {}
	Subscriptions: {}
	['', 'Apps', 'Logging'] > 
	['', 'Apps', 'Logging'] > ls logged_items

How did we do this? You can find the source for the logging app, and other personis clients, at https://github.com/jbu/personis/tree/master/clients/ (log-llum is the cherrypy version, aelog is the version that runs on appengine). Look at the method log_me in https://github.com/jbu/personis/blob/master/clients/log-llum/log-llum.py::

    @cherrypy.expose
    def log_me(self, item):
        if cherrypy.session.get('um') == None:
            raise cherrypy.HTTPError(400, 'Log in first.')
        um = cherrypy.session.get('um')
        ev = client.Evidence(source='llum-log', evidence_type="explicit", value=item, time=time.time())
        um.tell(context=['Apps','Logging'], componentid='logged_items', evidence=ev)
        raise cherrypy.HTTPRedirect('/')

As you can see, the work is done by two lines. One creates the evidence that something happened, and the next tells the model about it.
We will now do a similar exercise.

* Create a new directory (u:\\comp5047\\asker). 
* Save https://raw.github.com/jbu/personis/master/clients/asker/client_secrets.json into the new directory. 
* Copy this code skeleton into a file in the directory called ask.py::

	from personis import client
	import httplib2
    p = httplib2.ProxyInfo(proxy_type=httplib2.socks.PROXY_TYPE_HTTP_NO_TUNNEL, proxy_host='www-cache.it.usyd.edu.au', proxy_port=8000)
    um = client.util.LoginFromClientSecrets(http=httplib2.Http(proxy_info=p))

If we execute it

	\comp5047\Scripts\python.exe ask.py

it should take you through an authentication routine (involving web browsers, google, and a personis server) and then exit.

Lets say we want to ask the model what we have been eating (assuming we have been logging our meals with the logging app shown above)

	   kiwi : ***
	  grape : *
	  apple : **
	   pear : ****
	 orange : ***
	 banana : *

Can you add to ask.py to replicate this? You will probably need to use umbrowser to discover the model structure.