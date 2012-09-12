#!/usr/local/bin/python

import Personis_base
from Personis_util import printcomplist

print("tell new location for Alice")
um = Personis_base.Access(model='Alice', modeldir='Tests/Models', user='alice', password='secret')
# create a piece of evidence with home as value
ev = Personis_base.Evidence(evidence_type="explicit", value="home")
# tell this as user alice's location
um.tell(context=['Location'], componentid='location', evidence=ev)

print("===================================================================")
print("Now check the evidence list for Alice's location")
reslist = um.ask(context=['Location'], view=['location'], resolver={'evidence_filter':"all"})
printcomplist(reslist, printev = "yes")

