
Application Program Interface
=============================

See :doc:`personis` for API documentation.

Examples
--------

Models can be accessed either locally in the filesystem, or via a server. 

Local access is via the `base` module, remote access vi `client`.  

Basic connection - get a handle to UM
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In a local setup::

	import base
	
	# access the model in the filesystem
	# model name is "alice", model is stored in directory "Models"
	um = base.Access(model="alice", modeldir='Models', user='contactapp')

And here's how to do it with a remote server::

	from personis import client

	# there is a similar client.Access() method, but we use a handy utility 
	# that gets the server information from a .json file and automates the login
	# process.
	um = client.util.LoginFromClientSecrets('client_secrets.json')

After this, the `um` object has almost identical behaviour in both cases.

Basic accretion operation - tell some evidence
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following example shows the use of `base` to *tell* a piece of evidence 
containing a name string to a component in the model.  The source of the evidence is "contactapp" which will have
been given access to the model by the owner.

::

	import base
	
	# access the model in the filesystem
	# model name is "alice", model is stored in directory "Models"
	um = base.Access(model="alice", modeldir='Models', user='contactapp')

	# create a piece of evidence with Alice as value
	ev = Personis_base.Evidence(evidence_type="explicit", value="Alice")

	# tell this as user alice's first name into component "firstname", context "Personal"
	um.tell(context=["Personal"], componentid="firstname", evidence=ev)


Basic resolution operation - ask for a value
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This example *ask*s for the value of a component using the default resolver that uses the most recent piece of 
evidence.

::

	import base
	
	um = base.Access(model="alice", modeldir='Models', user='contactapp')

	# now ask for the value of the component using the default resolver and the last piece of evidence
	reslist = um.ask(context=["Personal"], view=["firstname"], resolver=dict(evidence_filter="last1"))
	
A *view* is just a list of components. The list can be explicit in the ask request or we can give a view a 
name and store it in the model.

For example::

	# now ask for the value of two components using a view
	reslist = um.ask(context=["Personal"], view=["firstname", "lastname"], resolver=dict(evidence_filter="last1"))

We can make a view using a view object and the *mkview* method. For example::


	import base
	
	um = base.Access(model="alice", modeldir='Models', user='contactapp')

	vobj = Personis_base.View(Identifier="fullname", component_list=["firstname", "lastname"])
	um.mkview(context=["Personal"], viewobj=vobj)

	reslist= um.ask(context=["Personal"], view = 'fullname', resolver={'evidence_filter':"all"})

The values are returned by an ask request in a list of component objects, one for eachc component value requested.
The component objects have the attributes described in the documentation above but this includes 
a *value* attribute  which is the resolved value for the component. Eg::

	reslist = um.ask(context=["Personal"], view=["firstname"], resolver=dict(evidence_filter="last1"))
	print "Firstname:", reslist[0].value

Creating new contexts and components
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *mkcontext* and *mkcomponent* methods, along with the *Component* and *Context* objects, are used to build
new elements in the model. Here is an example of creating and then deleting a context::

	# assume we have accessed the model
	print "creating context 'Deltest' in context 'Personal'"
	cobj = base.Context(Identifier="Deltest", Description="testing context deletion")
	# now make the new context
	um.mkcontext(context=["Personal"], contextobj=cobj)
	
	print "now delete it"
	um.delcontext(context=["Personal", "Deltest"]):

and here is an example of creating and then deleting a component::


	cobj = base.Component(Identifier="age", component_type="attribute", Description="age", goals=[['Personal', 'Health', 'weight']], value_type="number")
	
	um.mkcomponent(context=["Personal"], componentobj=cobj)
	
	# tell some evidence to the new component
	ev = Personis_base.Evidence(evidence_type="explicit", value=17)
	um.tell(context=["Personal"], componentid='age', evidence=ev)
	reslist = um.ask(context=["Personal"], view=['age'], resolver={'evidence_filter':"all"})
	print "Age:", reslist[0].value
	
	# delete the component
	resd = um.delcomponent(context=["Personal"], componentid = "age")
	
Navigating the Model
~~~~~~~~~~~~~~~~~~~~

If you want to discover what contexts are present in the model there is a variant on the *ask* method that 
allows you to get a list of all the *contexts*, *components*, *views* and *subscriptions* that are 
contained in a given context. Just add the parameter "showcontexts=True" to the *ask* call.
Using this call you can start at the root context and walk the tree of contexts discovering the full 
contents of the model. Eg::

	print "Show the root context"
	info = um.ask(context=[""], showcontexts=True)

The return value is a tuple containing (componentlist, contextlist, viewlist, sublist), where each part 
of the tuple is a list of objects.

Subscriptions: rules for action
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A feature of Personis is the ability to add a rule to a component that is examined when ever a *tell* operation
is performed on the component. The rule typically examines a resolved value of the component, matching against a 
pattern. If the pattern is matched an action is initiated. The action can be a *tell* operation to tell some 
evidence to a component, or a *notify* operation that will construct a URL and fetch it, thus initiating some 
action at an external web site.  Rules can be deleted using the *delete_sub* method.

Note: When a model fires a subscription it more or less bypasses security when it's just in one model. There is
the start of a scheme to have inter-model subscriptions based on the app security model (subscriptions log in
as an app/password) but this is not yet fully tested.

For example::

	from personis import client
	
	um = client.util.LoginFromClientSecrets()

	# subscription rule that will match firstname against a wildcard pattern (regular expression):
	sub = """
	<default!./Personal/firstname> ~ '.*' :
	         NOTIFY 'http://www.myweb.me/~alice/action.cgi?' 'firstname=' <./Personal/firstname> 
	"""
	
	# a token identifying the rule is returned
	subtoken = um.subscribe(context=["Personal"], view=['firstname'], subscription={'user':'alice', 'password':'secret', 'statement':sub})
	
	ev = Personis_base.Evidence(evidence_type="explicit", value="Alice")
	# do a tell. This should cause the action.cgi script to be invoked with the firstame
	um.tell(context=["Personal"], componentid='firstname', evidence=ev)

	# delete the rule
	um.delete_sub(context=["Personal"], componentid='lastname', subname=subtoken)

	
Import and Export of Models
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Models can be imported and exported in JSON (JavaScript Object Notation)
form using the *export_model* and *import_model* methods::

	import base
	import active
	
	um = active.Access(model="alice", modeldir='Models', user='contactapp')
	
	# export a model sub tree to JSON
	# note that all evidence will also be exported.
	modeljson = um.export_model(["Personal"], evidence_filter="all")
	print modeljson
	
	# import the same model tree but into a different context.
	um.import_model(context=["Temp"], partial_model=modeljson)
	
Simple App Interface
--------------------

In some cases we don't want the overhead of oauth (for instance, arduino-powered minimal-ui artifacts). In these cases there is a 
simpler mechanism to ask or tell based on app permissions. The general idea is to register an app, and then send raw Personis JSON requests
using a model/username/password authentication scheme. In the following example the modelname is my model, the 'user' parameter is set to the
app name, and the password is given. The app has been preregistered with the model and given permissions to ask at the given context. ::

	from personis import client
	um = client.util.LoginFromClientSecrets(...)
	appdetails = self.um.registerapp(app="MyHealth", desc="My Health Manager", password="pass9")
	self.um.setpermission(context=["HealthData"], app="MyHealth", permissions={'ask':True, 'tell':True})

Then, in the client ::

    from personis import app_client
    cli = app_client.Model(self.server_uri, model='mymodel', app='MyHealth', password='pass9')
    res = cli.ask(context=["HealthData"], view=['weight'])

Or leaving out the app_client utility library and using raw json::

    h = httplib2.Http(disable_ssl_certificate_validation=True) # an http object. We can add proxy or certificate validation here if needed.

    # My personis request. 
    data = {'modelname': 'mymodel', 'context': ['HealthData'], 'view': ['weight'], 'version': '11.2', 'user': 'MyHealth', 
        'resolver': {'evidence_filter': 'all'}, 'password': 'pass9', 'showcontexts': True}
    
    # Send the request (note the /ask endpoint)
    resp, content = h.request("https://s0.personis.name/ask", "POST", json.dumps(data))
    
    # receive the json response, and in this case check (it was a unit test)
    c = json.loads(content)
    self.assertEquals(c['val'][0][0]['Description'], 'My Weight')
