#!/usr/bin/env python

import Personis_base
from Personis_util import printcomplist

# add some evidence to some components - use example1_asks to see it

print "add evidence to Alice's model"
um = Personis_base.Access(model="Alice", modeldir='Tests/Models', user='alice', password='secret')
# create a piece of evidence with Alice as value
ev = Personis_base.Evidence(evidence_type="explicit", value="Alice")
# tell this as user alice's first name
um.tell(context=["Personal"], componentid='firstname', evidence=ev)
ev = Personis_base.Evidence(evidence_type="explicit", value="Smith")
um.tell(context=["Personal"], componentid='lastname', evidence=ev)
ev = Personis_base.Evidence(evidence_type="explicit", value="female")
um.tell(context=["Personal"], componentid='gender', evidence=ev)


print "==================================================================="
print "Now check the evidence list for Alice's names"
reslist = um.ask(context=["Personal"], view='fullname', resolver={'evidence_filter':"last1"})
printcomplist(reslist, printev = "yes")

print "Now check the evidence list for gender"
reslist = um.ask(context=["Personal"], view=['gender'], resolver={'evidence_filter':"last1"})
printcomplist(reslist, printev = "yes")

