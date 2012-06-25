#!/usr/bin/env python

import Personis
import Personis_base
from Personis_util import printcomplist

# add some evidence to some components - use example1_asks to see it

print ">>>> add evidence of Alice's names to his model"
um = Personis.Access(model="Alice", user='alice', password='secret')
	
# create a piece of evidence with demoex2 as source and Alice as value
ev = Personis_base.Evidence(source="demoex2", evidence_type="explicit", value="Alice")
# tell this as user Alice's first name
um.tell(context=["Personal"], componentid='firstname', evidence=ev)
ev = Personis_base.Evidence(source="demoex2", evidence_type="explicit", value="Smith")
um.tell(context=["Personal"], componentid='lastname', evidence=ev)


print "==================================================================="
print ">>>> Now check the evidence list for Alice's names"
reslist = um.ask(context=["Personal"], view='fullname')
printcomplist(reslist, printev = "yes")

