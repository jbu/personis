
Model Definition Format
=======================

When creating a new model it is possible to build the tree of contexts and components from a template file 
in "Model Definition Format" or "modeldef". This is useful when installing applications that need their
own subtree of contexts and components. The subtree could be built by the application using the *mkcontext*
and *mkcomponent* methods but there is also a "bulk" creation script (Src/Utils/mkmodel.py)
that reads "modeldef" files and creates the specified contexts, components, views, subscriptions 
and initial evidence.

Modeldef files consist of a series text lines. Lines that start with # are comments and ignored. 

Lines that start with @@ specify a context to be made. The context name is in the form of a pathname starting
at the root of the model. For example::

	@@Personal: description="Personal information"

This specifies a context called "Personal" in the root context of the model.
::

	@@Personal/Health: description="Health information"

This specifies a context called "Health" in the "Personal" context of the model.

A short string description of the context must be included.

After a context (@@) line, that context becomes the *current* context and any additional non-context elements 
are created in that context until the current context is changed by another @@ line.

Components are specified using lines that begin with two minus signs (--). For example::

	--firstname: type="attribute", value_type="string", description="First name", [evidence_type="explicit", value="Alice"]

this line specifies that a new component called "firstname" is created in the current context. 
Attributes of the component are specified using name=value elements. 
Initial evidence for the component is included as a sequence of bracketed sections as shown.

Subscription rules can also be included with a new component using the "rule" attribute. Eg::

	--email: type="attribute", value_type="string", description="email address",
	# create a subscription that will notify when email address changes
		rule="<default!./Personal/email> ~ '*' : NOTIFY 'http://www.somewhere.com/' 'email=' <./Personal/email>"

lines can be continued by breaking them after a comma.

Views are specified by lines starting with "==" and include a list of component pathnames. Eg::

	==fullname: firstname, lastname


