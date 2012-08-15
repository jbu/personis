#!/usr/bin/env python2.4

# NOTE: this test can only be run locally since
# it adds a new resolver.
import Personis_base
from Personis_util import printcomplist

# add some evidence to some components and then use example1 to see it

um = Personis_base.Access(model="Alice", modeldir="Tests/Models", user="alice", password='secret')
# create a piece of evidence with Carrol as value
ev = Personis_base.Evidence(evidence_type="explicit", value="Carrol")
# tell this as user alice's first name
um.tell(context=["Personal"], componentid='firstname', evidence=ev)
ev = Personis_base.Evidence(evidence_type="explicit", value="Smith")
um.tell(context=["Personal"], componentid='lastname', evidence=ev)

print("===================================================================")
print("Now add a new resolver to um")

def myresolver(model=None, component=None, context=None, resolver_args=None):
	"""     new resolver function 
	"""
	print("new resolver called with ", repr(component))
	if resolver_args == None:
		ev_filter = None
	else:
		ev_filter = resolver_args.get('evidence_filter')
	component.evidencelist = component.filterevidence(model=model, context=context, resolver_args=resolver_args)
	if len(component.evidencelist) > 0:
		component.value = component.evidencelist[-1]['value']
	return component

um.resolverlist["myresolver"] = myresolver

print("now ask for fullname")
reslist = um.ask(context=["Personal"], view='fullname', resolver={"resolver":"myresolver", "evidence_filter":"all"})
print("and print result")
printcomplist(reslist, printev = "yes")

