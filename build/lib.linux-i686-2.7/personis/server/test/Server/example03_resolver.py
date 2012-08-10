#!/usr/bin/env python

import Personis
import Personis_base
from Personis_util import printcomplist

print ">>>> add some evidence to some components and then use example1 to see it"

um = Personis.Access(model="Alice", user='alice', password='secret')

print ">>>> create a piece of evidence with alice as source and Alice as value"
ev = Personis_base.Evidence(source="willy", evidence_type="explicit", value="Fred")
print ">>>> tell this as user alice's first name"
um.tell(context=["Personal"], componentid='firstname', evidence=ev)

ev = Personis_base.Evidence(source="nilly", evidence_type="explicit", value="Smith")
um.tell(context=["Personal"], componentid='lastname', evidence=ev)

print "==================================================================="
print ">>>> Now check the evidence list for Alice's names"
reslist = um.ask(context=["Personal"], view='fullname')
printcomplist(reslist, printev = "yes")

