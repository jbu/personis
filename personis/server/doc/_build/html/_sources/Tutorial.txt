

Tutorial Introduction to Personis
=================================

This tutorial assumes you have installed the framework using the instructions in the Installation section.
Using the *umbrowser* command line utility, the tutorial will take you through the construction, navigation and 
management of a user model.

umbrowser
---------

The umbrowser.py program is a commandline utility that allows most
operations of the Personis system to be carried out interactively.

Umbrowser is found in the main Personis directory and is started with
the command ./umbrowser.py::

	$ ./umbrowser.py
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


To create or access a model you need to specify a username and password
using the login command::


	[''] > help login
	login username password
	[''] > login alice secret
	username: alice
	password: secret


To operate on models stored in the local file system we use the "base"
command. To operate on models stored on a remote server we user the
"server" command. For now we will use "base" since we can only make new models in the local file system, 
not remotely::

	[''] > base


Now we make a model for alice in the current directory (.) using the
mkmodel command::

	[''] > help mkmodel
	 mkmodel model_name [model_directory]
		makes a new empty model
		uses username, password specified in login cmd

	[''] > mkmodel Alice .

	making model 'Alice' in directory '.' with username 'alice' and password 'secret'
	model made
	to access the model, use the command 'model Alice .'



Note that we called the model "Alice". This could be the same as the login
name but that is not necessary. For example user alice might want to make a
model for a temperature sensing device and might call the model "Temp".
Model names are case sensitive, so "Alice" is not the same as "alice".

Also, we could have put the model anywhere in the file system but chose
to put it in the current directory (.). The model is actually store in a
directory with the same name as the model. So, after the mkmodel command
there will be a new directory called "Alice" in our current directory.

Now we want to access the new model, so we use the "model" command::

	 [''] > model Alice .
	model 'Alice' open, access type is 'base'

and now we can see what is in the model (should be empty)::

	Alice [''] > ls
	Components:
	Contexts: []
	Views: {}
	Subscriptions: {}

The "ls" command is a like the Unix ls command: it lists what is in the
current context.
As you can see, the model is empty - no components, contexts, views or
subscriptions.
So let's make a new context called "Prefs" in the current (root) context::

	Alice [''] > mkcontext Prefs
	Context description? My preferences
	Create new context 'Prefs' in context '['']' with description 'My preferences'
	Ok?[N] Y

	Alice [''] > ls
	Components:
	Contexts: ['Prefs']
	Views: {}
	Subscriptions: {}

Now we will change context to the new "Prefs" context and make a
component "food" for our food preferences::

	Alice [''] > cd Prefs
	
	Alice ['', 'Prefs'] > mkcomponent food
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
	
	Alice ['', 'Prefs'] > ls
	Components:
		food: type of food I prefer
	Contexts: []
	Views: {}
	Subscriptions: {}
	
	Alice ['', 'Prefs'] > 

Now we have a model called "Alice", owned by "alice" that has one
context "Prefs" containing one component "food".
Now, Alice likes Thai food so we will add some evidence to her food
preference component using the "tell" command::

	Alice ['', 'Prefs'] > tell food
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

	
	Alice ['', 'Prefs'] > ls
	Components:
		food: type of food I prefer
	Contexts: []
	Views: {}
	Subscriptions: {}

We can now examine the "food" component with the "ls" command::

	Alice ['', 'Prefs'] > ls food
	===================================================================
	Component:  type of food I prefer
	===================================================================
	showobj:
	  Description = type of food I prefer
	  component_type = preference
	  evidencelist = 1 items
	  value_list = []
	  value = Thai
	  value_type = string
	  goals = []
	  resolver = None
	  Identifier = food
	  objectType = Component
	---------------------------------
	Evidence about it
	---------------------------------
	showobj:
	           comment = None
	           evidence_type = explicit
	           value = Thai
	           objectType = Evidence
	           source = alice
	           flags = ['']
	           time = Thu Apr 28 18:08:55 2011 (1304003335.61)
	           owner = alice
	           exp_time = 0
	           useby = None
	---------------------------------
	
Try doing the "tell" operation again with a different food preference and then "ls food" to see the additional
evidence that has been accreted.


To quit the model browser, use the *quit* command.

