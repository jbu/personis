#!/usr/bin/env python

import Personis_base
from Personis_util import printcomplist

# add some evidence to some components 

um = Personis_base.Access(model="Alice", modeldir='Tests/Models', user='alice', password='secret')

# create a piece of evidence with Carrol as value
ev = Personis_base.Evidence(evidence_type="explicit", value="Carrol")
# tell this as user alice's first name
um.tell(context=["Personal"], componentid='firstname', evidence=ev)

ev = Personis_base.Evidence(evidence_type="explicit", value="Smith")
um.tell(context=["Personal"], componentid='lastname', evidence=ev)

print("===================================================================")
print("Now check the evidence list for Alice's names")
reslist = um.ask(context=["Personal"], view='fullname')
printcomplist(reslist, printev = "yes")

